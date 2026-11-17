import argparse
import datetime
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from shortfall import agent, freeze, ledger, redact, score
from shortfall.budget import TOTAL_DOLLAR_CAP
from shortfall.pin import read_pin
from shortfall.trialscore import score_trial

PLAN_SCHEMA = "shortfall.plan/v1"
ENGINE_NAME = "colima-shortfall"
ENGINE_PROFILE = "shortfall"
MIN_FREE_BYTES = 5 * 1024**3
MIN_ROOM = 0.10
ORDERS = ("round-robin",)
WORDS_FILE = Path(".git") / "info" / "private-words"
DASHES = re.compile("[\u2013\u2014]")
QUOTE_WINDOW = 12


class PlanError(ValueError):
    pass


@dataclass(frozen=True)
class Cell:
    issue: str | None
    feedback: str

    @property
    def label(self) -> str:
        return f"{self.issue or 'unguided'}-{self.feedback}"


@dataclass(frozen=True)
class TrialSpec:
    id: str
    cell: Cell
    number: int


@dataclass
class Plan:
    path: Path
    name: str
    model: str
    mode: str
    cells: list[Cell]
    trials_per_cell: int
    caps: agent.Caps
    dollar_cap: float
    prompt_hash: str
    oversold_pin: str
    images: dict[str, str]
    order: str
    export_root: Path
    script: Path | None = None


def load_plan(root: Path, path: Path) -> Plan:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != PLAN_SCHEMA:
        raise PlanError(f"a plan needs schema {PLAN_SCHEMA}")
    name = data.get("name")
    if not (isinstance(name, str) and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name)):
        raise PlanError("name must be kebab-case")
    if data.get("mode") not in ledger.TASK_MODES:
        raise PlanError(f"mode must be one of {', '.join(ledger.TASK_MODES)}")
    cells = []
    for c in data.get("cells") or []:
        issue = None if c.get("issue") is None else str(c["issue"])
        if c.get("feedback") not in ledger.FEEDBACK_MODES:
            raise PlanError(f"feedback must be one of {', '.join(ledger.FEEDBACK_MODES)}")
        if (issue is None) != (data["mode"] == "unguided"):
            raise PlanError("guided cells need an issue and unguided cells none")
        cells.append(Cell(issue, c["feedback"]))
    if not cells or len({c.label for c in cells}) != len(cells):
        raise PlanError("cells must be a non-empty list without repeats")
    caps = data.get("caps") or {}
    order = data.get("order", "round-robin")
    if order not in ORDERS:
        raise PlanError(f"order must be one of {', '.join(ORDERS)}")
    script = data.get("script")
    plan = Plan(
        path=Path(path),
        name=name,
        model=str(data.get("model")),
        mode=data["mode"],
        cells=cells,
        trials_per_cell=int(data.get("trials_per_cell", 0)),
        caps=agent.Caps(
            runs=int(caps.get("runs", agent.RUN_CAP)),
            attempts=int(caps.get("attempts", agent.ATTEMPT_CAP)),
            turns=int(caps.get("turns", agent.TURN_CAP)),
            dollars=float(caps.get("dollars", 0.0)),
        ),
        dollar_cap=float(data.get("dollar_cap", 0.0)),
        prompt_hash=str(data.get("prompt_hash")),
        oversold_pin=str(data.get("oversold_pin")),
        images={str(k): str(v) for k, v in (data.get("images") or {}).items()},
        order=order,
        export_root=Path(root) / data.get("export_root", f"benchmark/agent/{name}"),
        script=None if script is None else Path(root) / script,
    )
    if plan.trials_per_cell < 1:
        raise PlanError("trials_per_cell must be at least 1")
    if plan.dollar_cap > TOTAL_DOLLAR_CAP:
        raise PlanError(f"dollar_cap cannot be above {TOTAL_DOLLAR_CAP:.2f}")
    if plan.model == "scripted" and plan.script is None:
        raise PlanError("a scripted plan needs a script")
    if not plan.images:
        raise PlanError("a plan lists the image ids it expects")
    return plan


def trial_order(plan: Plan) -> list[TrialSpec]:
    return [
        TrialSpec(f"{cell.label}-{k}", cell, k)
        for k in range(1, plan.trials_per_cell + 1)
        for cell in plan.cells
    ]


def issue_stem(root: Path, issue: str | None) -> str | None:
    if issue is None:
        return None
    pattern = re.compile(rf"issues/{re.escape(issue)}\b")
    for p in sorted((Path(root) / "snapshots" / "issues").glob("*.md")):
        if any(pattern.search(line) for line in p.read_text(encoding="utf-8").splitlines()[:5]):
            return p.stem
    raise PlanError(f"no bug report snapshot for issue {issue}")


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


class State:
    def __init__(self, root: Path, plan: Plan):
        self.root = Path(root)
        self.plan = plan
        self.folder = self.root / "runs" / "trials" / plan.name
        self.folder.mkdir(parents=True, exist_ok=True)
        self.events_path = self.folder / "events.jsonl"
        self.pid_path = self.root / "runs" / "trials" / f"{plan.name}.pid"

    def events(self) -> list[dict]:
        if not self.events_path.exists():
            return []
        return [json.loads(x) for x in self.events_path.read_text().splitlines() if x.strip()]

    def add(self, event: str, **fields) -> None:
        line = json.dumps({"event": event, **fields, "time": now()}, ensure_ascii=False)
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(redact.mask(line) + "\n")
        print(f"{now()} {event} {json.dumps(fields, ensure_ascii=False)}", flush=True)

    def run_ids(self) -> list[str]:
        return [e["run_id"] for e in self.events() if e["event"] == "trial-start"]

    def trial(self, spec: TrialSpec, records: list[dict]) -> dict:
        events = [e for e in self.events() if e.get("trial") == spec.id]
        ended = {r["trial_id"] for r in records if r.get("kind") == "agent-end"}
        starts = [e["run_id"] for e in events if e["event"] == "trial-start"]
        return {
            "exported": any(e["event"] == "trial-exported" for e in events),
            "held": any(e["event"] == "trial-held" for e in events),
            "kept_local": any(e["event"] == "trial-kept-local" for e in events),
            "finished": [r for r in starts if r in ended],
            "unfinished": [r for r in starts if r not in ended],
            "logged_interrupted": {
                e["run_id"] for e in events if e["event"] == "trial-interrupted"
            },
        }


def plan_spend(records: list[dict], run_ids: list[str]) -> dict:
    mine = [r for r in records if any(r["attempt_id"].startswith(i) for i in run_ids)]
    return ledger.spent(mine)


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def engine_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k != "DOCKER_CONTEXT"}
    env["DOCKER_HOST"] = f"unix://{Path.home()}/.colima/{ENGINE_PROFILE}/docker.sock"
    return env


def engine_name() -> str:
    proc = subprocess.run(
        ["docker", "info", "--format", "{{.Name}}"],
        env=engine_env(),
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def vm_free_bytes() -> int | None:
    proc = subprocess.run(
        ["colima", "ssh", "--profile", ENGINE_PROFILE, "--", "df", "-Pk", "/var/lib/docker"],
        capture_output=True,
        text=True,
    )
    rows = proc.stdout.strip().splitlines()
    if proc.returncode != 0 or len(rows) < 2:
        return None
    return int(rows[-1].split()[3]) * 1024


def oversold_running() -> bool:
    proc = subprocess.run(["pgrep", "-f", "bin/oversold run"], capture_output=True, text=True)
    return bool(proc.stdout.strip())


@dataclass
class Checks:
    engine_name: Callable[[], str] = engine_name
    image_id: Callable[[str, str | None], str] = field(default=None)
    vm_free_bytes: Callable[[], int | None] = vm_free_bytes
    mac_free_bytes: Callable[[Path], int] = lambda root: shutil.disk_usage(root).free
    oversold_running: Callable[[], bool] = oversold_running


def preflight(root: Path, plan: Plan, cap: float, checks: Checks) -> list[str]:
    problems = []
    name = checks.engine_name()
    if name != ENGINE_NAME:
        problems.append(f"engine reports {name or 'nothing'}, expected {ENGINE_NAME}")
    else:
        for tag, want in sorted(plan.images.items()):
            version, _, variant = tag.partition("-")
            got = checks.image_id(version, variant or None)
            if got != want:
                problems.append(f"image {tag} is {got or 'missing'}, the plan expects {want}")
        free = checks.vm_free_bytes()
        if free is None or free < MIN_FREE_BYTES:
            problems.append(f"the engine VM has {fmt_bytes(free)} free, 5 GB needed")
        if checks.oversold_running():
            problems.append("another Oversold run is still going")
    current = freeze.prompt_hash(root)
    recorded = freeze.recorded_hash(root)
    if not (current == recorded == plan.prompt_hash):
        problems.append(
            f"prompt hash {current} does not match the plan's {plan.prompt_hash} "
            f"and the recorded {recorded}"
        )
    pin = read_pin(Path(root) / "oversold.lock")[1]
    if plan.oversold_pin != pin:
        problems.append(f"the plan's Oversold pin {plan.oversold_pin} is not oversold.lock's {pin}")
    free = checks.mac_free_bytes(root)
    if free < MIN_FREE_BYTES:
        problems.append(f"the Mac has {fmt_bytes(free)} free, 5 GB needed")
    records = ledger.load(score.ledger_path_for(root))
    need = 0.0 if plan.model == "scripted" else MIN_ROOM
    room = rooms(records, State(root, plan).run_ids(), cap)
    if room["plan"] < need:
        problems.append(f"no dollar room under the plan cap: {room['plan']:.4f} left")
    if room["total"] < need:
        problems.append(f"no dollar room under the {TOTAL_DOLLAR_CAP:.0f} dollar total")
    return problems


def rooms(records: list[dict], run_ids: list[str], cap: float) -> dict:
    return {
        "plan": cap - plan_spend(records, run_ids)["dollars"],
        "total": TOTAL_DOLLAR_CAP - ledger.spent(records)["dollars"],
    }


def fmt_bytes(n: int | None) -> str:
    return "unknown" if n is None else f"{n / 1024**3:.1f} GB"


def stop_reason(end_reason: str | None, trial_cap_was_plan_room: bool) -> str | None:
    reason = end_reason or ""
    if reason.startswith(("stopped:", "leak guard:", "model API stopped the trial:")):
        return reason
    if reason.startswith("dollar cap:") and (trial_cap_was_plan_room or "total dollars" in reason):
        return reason
    return None


def local_markers() -> list[str]:
    temp = tempfile.gettempdir()
    found = {str(Path.home()), temp, os.path.realpath(temp)}
    return sorted(m for m in found if len(m) > 1)


def texts(folder: Path):
    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        data = gzip.decompress(p.read_bytes()) if p.suffix == ".gz" else p.read_bytes()
        yield p, data.decode("utf-8", errors="replace")


class Quotes:
    def __init__(self, root: Path):
        self.root = Path(root)
        self._lines: dict[str, list[str]] = {}

    def lines(self, word: str) -> list[str]:
        if word not in self._lines:
            found = []
            snapshots = self.root / "snapshots"
            sources = [snapshots / "medusa-2.22.0", snapshots / "issues"]
            for source in sources:
                proc = subprocess.run(
                    ["grep", "-rhiF", "--", word, str(source)], capture_output=True, text=True
                )
                found += proc.stdout.splitlines()
            self._lines[word] = found
        return self._lines[word]

    def quoted(self, text: str, start: int, end: int, word: str) -> bool:
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        line_end = len(text) if line_end < 0 else line_end
        left = text[max(line_start, start - QUOTE_WINDOW) : end].split("\t")[-1]
        right = text[start : min(line_end, end + QUOTE_WINDOW)]
        lines = self.lines(word)
        return any(left in line for line in lines) or any(right in line for line in lines)


def decoded(text: str) -> str:
    out = []
    for raw in text.splitlines():
        try:
            out.append(json.dumps(json.loads(raw), ensure_ascii=False, indent=0))
        except (json.JSONDecodeError, ValueError):
            out.append(raw)
    flat = "\n".join(out)
    return flat.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')


def private_words(root: Path) -> list[str] | None:
    path = Path(root) / WORDS_FILE
    if not path.is_file():
        return None
    lines = (x.strip().lower() for x in path.read_text(encoding="utf-8").splitlines())
    return [x for x in lines if x]


def scan_export(
    root: Path, folder: Path, quotes: Quotes, key: str | None, words: list[str] | None
) -> list[str]:
    problems = []
    if words is None:
        problems.append(f"no private word list at {WORDS_FILE}")
    for path, text in texts(folder):
        rel = path.relative_to(folder)
        for marker in local_markers():
            if marker in text:
                problems.append(f"{rel}: holds a local path")
        if key and key in text:
            problems.append(f"{rel}: holds the API key")
        for pattern in redact.PATTERNS:
            if pattern.search(text):
                problems.append(f"{rel}: holds something that looks like a key")
        if path.suffix != ".gz" and DASHES.search(text):
            problems.append(f"{rel}: holds a raw dash character")
        flat = decoded(text)
        low = flat.lower()
        for word in words or []:
            for m in re.finditer(re.escape(word), low):
                if not quotes.quoted(flat, m.start(), m.end(), word):
                    problems.append(f"{rel}: {word!r} that is not a quote of Medusa or a report")
                    break
    problems += gitleaks_findings(root, folder)
    return sorted(set(problems))


def gitleaks_findings(root: Path, folder: Path) -> list[str]:
    tool = shutil.which("gitleaks") or str(Path.home() / ".local" / "bin" / "gitleaks")
    if not Path(tool).exists():
        return ["gitleaks is not installed, so the export could not be scanned"]
    with tempfile.TemporaryDirectory(dir=Path(root) / "runs" / "trials") as tmp:
        unpacked = Path(tmp) / "unpacked"
        for path, text in texts(folder):
            out = unpacked / path.relative_to(folder)
            out = out.with_suffix("") if out.suffix == ".gz" else out
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
        report = Path(tmp) / "report.json"
        subprocess.run(
            [tool, "dir", "--no-banner", "--log-level", "error", "-r", str(report), str(unpacked)],
            capture_output=True,
            text=True,
        )
        if not report.exists():
            return ["gitleaks did not write a report"]
        found = json.loads(report.read_text() or "[]")
        known = snapshot_secrets(root, tool)
        return [
            f"{Path(f['File']).relative_to(unpacked)}: gitleaks {f['RuleID']}"
            for f in found
            if f.get("Secret") not in known
        ]


_SNAPSHOT_SECRETS: set[str] | None = None


def snapshot_secrets(root: Path, tool: str) -> set[str]:
    global _SNAPSHOT_SECRETS
    if _SNAPSHOT_SECRETS is None:
        with tempfile.TemporaryDirectory(dir=Path(root) / "runs" / "trials") as tmp:
            report = Path(tmp) / "snapshot.json"
            subprocess.run(
                [tool, "dir", "--no-banner", "--log-level", "error", "-r", str(report)]
                + [str(Path(root) / "snapshots")],
                capture_output=True,
                text=True,
            )
            found = json.loads(report.read_text() or "[]") if report.exists() else []
            _SNAPSHOT_SECRETS = {f.get("Secret") for f in found}
    return _SNAPSHOT_SECRETS


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=1, ensure_ascii=True) + "\n", encoding="ascii")


def transcript_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def export_trial(
    root: Path,
    run_id: str,
    dest: Path,
    records: list[dict],
    exporter: Callable[[str, Path], None],
) -> dict:
    root = Path(root)
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "runs").mkdir(parents=True)
    folders = []
    for r in records:
        if r.get("kind") == "final":
            folders += [f for f in r.get("run_folders") or [] if f not in folders]
    for folder in folders:
        exporter(folder, dest / "runs" / Path(folder).name)
    with (dest / "ledger.jsonl").open("w", encoding="ascii") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")
    source = root / "runs" / "agent" / run_id
    transcript = source / "transcript.jsonl"
    events = transcript_events(transcript)
    if transcript.exists():
        body = redact.mask(transcript.read_text(encoding="utf-8")).encode("utf-8")
        (dest / "transcript.jsonl.gz").write_bytes(gzip.compress(body, mtime=0))
    submitted = [
        c["arguments"]
        for e in events
        if e.get("event") == "reply"
        for c in e["message"]["tool_calls"]
        if c["name"] == "submit_attempt"
    ]
    scored = score_trial(root, records)
    (dest / "attempts").mkdir()
    attempt_list = []
    for a in scored["attempt_list"]:
        n = a["attempt"]
        ran = source / f"attempt-{n:02d}.yaml"
        if ran.exists():
            shutil.copy(ran, dest / "attempts" / ran.name)
        args = submitted[n - 1] if n - 1 < len(submitted) else {}
        pred = next((r for r in records if r.get("kind") == "prediction" and r["attempt"] == n), {})
        attempt_list.append(
            {
                **a,
                "hypothesis": pred.get("hypothesis"),
                "scenario_sha256": pred.get("scenario_sha256"),
                "scenario_file": f"attempts/{ran.name}" if ran.exists() else None,
                "submitted_scenario": args.get("scenario"),
            }
        )
    write_json(dest / "attempts.json", attempt_list)
    finish = next((e for e in reversed(events) if e.get("event") == "finish"), None)
    write_json(
        dest / "claims.json",
        {"summary": (finish or {}).get("summary"), "claims": scored["claims"]},
    )
    summary = {k: v for k, v in scored.items() if k != "attempt_list"}
    write_json(dest / "score.json", summary)
    return summary


class Runner:
    def __init__(
        self,
        root: Path,
        plan: Plan,
        cap: float,
        *,
        make_model: Callable[[], agent.Model] | None = None,
        runner: score.Runner | None = None,
        checks: Checks | None = None,
        exporter: Callable[[str, Path], None] | None = None,
        verifier: Callable[[Path], tuple[bool, str]] | None = None,
        scanner: Callable[[Path], list[str]] | None = None,
        validate: Callable[[Path, Path], tuple[bool, str]] = agent.validate_with_oversold,
    ):
        self.root = Path(root)
        self.plan = plan
        self.cap = min(cap, plan.dollar_cap)
        self.state = State(root, plan)
        self.oversold = runner or score.OversoldRunner(self.root)
        self.make_model = make_model or self.default_model
        self.checks = checks or Checks(image_id=self.image_id)
        if self.checks.image_id is None:
            self.checks.image_id = self.image_id
        self.exporter = exporter or self.oversold_export
        self.verifier = verifier or self.oversold_verify
        self.quotes = Quotes(self.root)
        self.validate = validate
        key = None
        env = self.root / ".env"
        if env.exists() and plan.model != "scripted":
            from shortfall.models import load_key

            key = load_key(env)
        words = private_words(self.root)
        self.scanner = scanner or (
            lambda folder: scan_export(self.root, folder, self.quotes, key, words)
        )

    def default_model(self) -> agent.Model:
        if self.plan.model == "scripted":
            items = json.loads(self.plan.script.read_text(encoding="utf-8"))
            return agent.ScriptedModel.from_json(items)
        from shortfall.models import AnthropicModel

        return AnthropicModel(self.plan.model, env_path=self.root / ".env")

    def image_id(self, version: str, variant: str | None) -> str:
        try:
            return self.oversold.lookup(version, variant)[0]
        except RuntimeError:
            return ""

    def oversold_export(self, folder: str, dest: Path) -> None:
        proc = subprocess.run(
            ["sh", "scripts/oversold.sh", "export", folder, str(dest)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"export of {Path(folder).name} failed")

    def oversold_verify(self, folder: Path) -> tuple[bool, str]:
        proc = subprocess.run(
            ["sh", "scripts/oversold.sh", "check", "--verify", str(folder)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr)[-300:]

    def records(self) -> list[dict]:
        return ledger.load(score.ledger_path_for(self.root))

    def stop(self, reason: str) -> int:
        self.state.add("plan-stop", reason=score.clean(reason, self.root))
        return 1

    def run(self) -> int:
        self.state.add("plan-start", plan=self.plan.name, dollar_cap=self.cap)
        for spec in trial_order(self.plan):
            records = self.records()
            st = self.state.trial(spec, records)
            if st["exported"] or st["held"] or st["kept_local"]:
                continue
            if st["finished"]:
                outcome = self.finish(spec, st["finished"][-1], records, False)
                if outcome:
                    return outcome
                continue
            for run_id in st["unfinished"]:
                if run_id not in st["logged_interrupted"]:
                    self.state.add("trial-interrupted", trial=spec.id, run_id=run_id)
            if len(st["unfinished"]) >= 2:
                return self.stop(f"trial {spec.id} was interrupted twice")
            problems = preflight(self.root, self.plan, self.cap, self.checks)
            if problems:
                return self.stop("; ".join(problems))
            room = rooms(records, self.state.run_ids(), self.cap)["plan"]
            trial_dollars = min(self.plan.caps.dollars, room)
            outcome = self.run_trial(spec, trial_dollars, trial_dollars < self.plan.caps.dollars)
            if outcome:
                return outcome
        self.state.add("plan-done", plan=self.plan.name)
        return 0

    def run_trial(self, spec: TrialSpec, dollars: float, lowered: bool) -> int:
        while True:
            stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
            run_id = f"agent-{stamp}"
            if not (self.root / "runs" / "agent" / run_id).exists():
                break
            time.sleep(1)
        self.state.add("trial-start", trial=spec.id, run_id=run_id, dollar_cap=dollars)
        caps = agent.Caps(
            runs=self.plan.caps.runs,
            attempts=self.plan.caps.attempts,
            turns=self.plan.caps.turns,
            dollars=dollars,
        )
        trial = agent.Trial(
            self.root,
            self.make_model(),
            self.oversold,
            trial_id=run_id,
            task_mode=self.plan.mode,
            feedback=spec.cell.feedback,
            issue=issue_stem(self.root, spec.cell.issue),
            caps=caps,
            image=self.oversold.image(agent.VERSION),
            pin=self.oversold.pin,
            validate=self.validate,
        )
        end = trial.run()
        self.state.add("trial-end", trial=spec.id, run_id=run_id, reason=end["reason"])
        return self.finish(spec, run_id, self.records(), lowered)

    def finish(self, spec: TrialSpec, run_id: str, records: list[dict], lowered: bool) -> int:
        mine = [r for r in records if r["attempt_id"].startswith(f"{run_id}-")]
        end = next(r for r in mine if r.get("kind") == "agent-end")
        stop = stop_reason(end["reason"], lowered)
        if stop and not end["reason"].startswith("dollar cap:"):
            self.state.add("trial-kept-local", trial=spec.id, run_id=run_id, reason=stop)
            return self.stop(f"trial {spec.id}: {stop}")
        scored = score_trial(self.root, mine)
        if scored["manual_check"]:
            self.state.add("trial-held", trial=spec.id, run_id=run_id, notes=scored["manual_check"])
            return self.stop(stop) if stop else 0
        dest = self.plan.export_root / spec.id
        try:
            export_trial(self.root, run_id, dest, mine, self.exporter)
            bad = []
            for folder in sorted((dest / "runs").iterdir()):
                ok, text = self.verifier(folder)
                if not ok:
                    bad.append(f"verify {folder.name}: {text.strip()[-120:]}")
            bad += self.scanner(dest)
        except (RuntimeError, OSError) as err:
            bad = [f"export: {err}"]
        if bad:
            shutil.rmtree(dest, ignore_errors=True)
            self.state.add("trial-export-failed", trial=spec.id, run_id=run_id, problems=bad)
            return self.stop(f"trial {spec.id} failed its export checks: {bad[0]}")
        self.state.add(
            "trial-exported",
            trial=spec.id,
            run_id=run_id,
            folder=score.relative(self.root, dest),
        )
        return self.stop(stop) if stop else 0


def status(root: Path, plan: Plan) -> dict:
    state = State(root, plan)
    events = state.events()
    records = ledger.load(score.ledger_path_for(root))
    run_ids = state.run_ids()
    spent = plan_spend(records, run_ids)
    done = [e["trial"] for e in events if e["event"] in ("trial-exported", "trial-held")]
    current = None
    for e in events:
        if e["event"] == "trial-start":
            current = e
        elif e["event"] in ("trial-end", "trial-interrupted") and current:
            if e.get("run_id") == current["run_id"]:
                current = None
    last = events[-1]["time"] if events else None
    if current:
        mine = [r for r in records if r["attempt_id"].startswith(f"{current['run_id']}-")]
        if mine:
            last = max([last or "", *(r.get("timestamp") or "" for r in mine)])
    pid = None
    alive = False
    if state.pid_path.exists():
        pid = int(state.pid_path.read_text().strip() or 0)
        alive = bool(pid) and pid_alive(pid)
    stops = [e for e in events if e["event"] in ("plan-stop", "plan-done")]
    return {
        "plan": plan.name,
        "trials": len(trial_order(plan)),
        "done": len(done),
        "done_trials": done,
        "current": current and {"trial": current["trial"], "run_id": current["run_id"]},
        "dollars": spent["dollars"],
        "unsettled_calls": spent["unsettled_calls"],
        "oversold_runs": spent["oversold_runs"],
        "last_event": last,
        "pid": pid,
        "alive": alive,
        "last_stop": stops[-1] if stops else None,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.trials")
    p.add_argument("plan")
    p.add_argument("--status", action="store_true")
    p.add_argument("--raise-dollar-cap", type=float, default=0.0)
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    plan = load_plan(root, Path(args.plan))
    if args.status:
        print(json.dumps(status(root, plan), indent=1))
        return 0
    state = State(root, plan)
    if state.pid_path.exists():
        text = state.pid_path.read_text().strip()
        pid = int(text) if text.isdigit() else 0
        if pid and pid not in (os.getpid(), os.getppid()) and pid_alive(pid):
            print(f"plan {plan.name} is already running as process {pid}")
            return 1
    os.setpgrp()
    return Runner(root, plan, args.raise_dollar_cap).run()


if __name__ == "__main__":
    sys.exit(main())
