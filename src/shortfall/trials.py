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

from shortfall import agent, control, freeze, ledger, redact, score
from shortfall.budget import TOTAL_DOLLAR_CAP
from shortfall.coverage import HELD_NOTE
from shortfall.pin import read_pin
from shortfall.trialscore import score_trial

PLAN_SCHEMA = "shortfall.plan/v1"
PLAN_SCHEMA_V2 = "shortfall.plan/v2"
REVIEW_RUNS = 60
REVIEW_FIX = "pr-17420"
WORD_FILES = Path(".git") / "info" / "private-word-files"
ENGINE_NAME = "colima-shortfall"
ENGINE_PROFILE = "shortfall"
MIN_FREE_BYTES = 5 * 1024**3
MIN_ROOM = 0.10
ORDERS = ("round-robin",)
WORDS_FILE = Path(".git") / "info" / "private-words"
ALLOW_FILE = Path(".git") / "info" / "private-word-allow"
MODEL_TEXT = "model text: "
ENTERPRISE = "enterprise: "
HOLDS = (MODEL_TEXT, ENTERPRISE, HELD_NOTE)
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
    cell: Cell | None
    number: int
    kind: str = "agent"
    variant: str = "v2"
    prompt_hash: str | None = None
    method: str | None = None
    mode: str = "unguided"


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
    specs: list[TrialSpec] = field(default_factory=list)
    baseline_runs: int = 300
    baseline_root: Path | None = None
    report: list[str] = field(default_factory=list)


def load_plan(root: Path, path: Path) -> Plan:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and data.get("schema") == PLAN_SCHEMA_V2:
        return load_plan_v2(root, path, data)
    if not isinstance(data, dict) or data.get("schema") != PLAN_SCHEMA:
        raise PlanError(f"a plan needs schema {PLAN_SCHEMA} or {PLAN_SCHEMA_V2}")
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
    plan.specs = [
        TrialSpec(f"{cell.label}-{k}", cell, k, prompt_hash=plan.prompt_hash, mode=plan.mode)
        for k in range(1, plan.trials_per_cell + 1)
        for cell in plan.cells
    ]
    return plan


def load_plan_v2(root: Path, path: Path, data: dict) -> Plan:
    name = data.get("name")
    if not (isinstance(name, str) and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name)):
        raise PlanError("name must be kebab-case")
    specs: dict[str, TrialSpec] = {}
    for arm in data.get("arms") or []:
        kind = arm.get("kind")
        if kind == "agent":
            if arm.get("prompts") not in agent.VARIANTS:
                raise PlanError(f"prompts must be one of {', '.join(agent.VARIANTS)}")
            if arm.get("mode") not in ledger.TASK_MODES:
                raise PlanError(f"mode must be one of {', '.join(ledger.TASK_MODES)}")
            if arm.get("feedback") not in ledger.FEEDBACK_MODES:
                raise PlanError(f"feedback must be one of {', '.join(ledger.FEEDBACK_MODES)}")
            issue = None if arm.get("issue") is None else str(arm["issue"])
            if (issue is None) != (arm["mode"] == "unguided"):
                raise PlanError("guided arms need an issue and unguided arms none")
            cell = Cell(issue, arm["feedback"])
            for n in arm.get("trials") or []:
                spec = TrialSpec(
                    f"{arm['name']}-{n}",
                    cell,
                    int(n),
                    "agent",
                    arm["prompts"],
                    str(arm.get("prompt_hash")),
                    None,
                    arm["mode"],
                )
                specs[spec.id] = spec
        elif kind == "baseline":
            if arm.get("method") not in ("grid", "random"):
                raise PlanError("a baseline arm's method is grid or random")
            for n in arm.get("seeds") or []:
                spec_id = f"{arm['method']}-seed-{n}"
                specs[spec_id] = TrialSpec(
                    spec_id, None, int(n), "baseline", "", None, arm["method"], "unguided"
                )
        else:
            raise PlanError("an arm's kind is agent or baseline")
    order = data.get("order") or []
    if sorted(order) != sorted(specs) or len(set(order)) != len(order):
        raise PlanError("order must list every trial of every arm exactly once")
    caps = data.get("agent_caps") or {}
    script = data.get("script")
    plan = Plan(
        path=Path(path),
        name=name,
        model=str(data.get("model")),
        mode="mixed",
        cells=[],
        trials_per_cell=0,
        caps=agent.Caps(
            runs=int(caps.get("runs", agent.RUN_CAP)),
            attempts=int(caps.get("attempts", agent.ATTEMPT_CAP)),
            turns=int(caps.get("turns", agent.TURN_CAP)),
            dollars=float(caps.get("dollars", 0.0)),
        ),
        dollar_cap=float(data.get("dollar_cap", 0.0)),
        prompt_hash="",
        oversold_pin=str(data.get("oversold_pin")),
        images={str(k): str(v) for k, v in (data.get("images") or {}).items()},
        order="explicit",
        export_root=Path(root) / data.get("export_root", f"benchmark/agent/{name}"),
        script=None if script is None else Path(root) / script,
        specs=[specs[i] for i in order],
        baseline_runs=int(data.get("baseline_runs", 300)),
        baseline_root=Path(root) / data.get("baseline_root", "benchmark/baselines/2004ed5"),
        report=[str(x) for x in data.get("report") or []],
    )
    if plan.dollar_cap > TOTAL_DOLLAR_CAP:
        raise PlanError(f"dollar_cap cannot be above {TOTAL_DOLLAR_CAP:.2f}")
    if plan.model == "scripted" and plan.script is None:
        raise PlanError("a scripted plan needs a script")
    if not plan.images:
        raise PlanError("a plan lists the image ids it expects")
    return plan


def trial_order(plan: Plan) -> list[TrialSpec]:
    return list(plan.specs)


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
        self.pause_path = self.root / "runs" / "trials" / f"{plan.name}.pause"

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
        reopened = [i for i, e in enumerate(events) if e["event"] == "trial-reopened"]
        if reopened:
            events = events[reopened[-1] + 1 :]
        if spec.kind == "baseline":
            ended = {
                e["run_id"] for e in events if e["event"] == "trial-end" and e.get("exit") == 0
            }
        else:
            ended = {r["trial_id"] for r in records if r.get("kind") == "agent-end"}
        starts = [e["run_id"] for e in events if e["event"] == "trial-start"]
        return {
            "reopened": len(reopened),
            "exported": any(e["event"] == "trial-exported" for e in events),
            "held": any(e["event"] == "trial-held" for e in events),
            "kept_local": any(e["event"] == "trial-kept-local" for e in events),
            "finished": [r for r in starts if r in ended],
            "unfinished": [r for r in starts if r not in ended],
            "logged_interrupted": {
                e["run_id"] for e in events if e["event"] == "trial-interrupted"
            },
        }


def reopen(root: Path, plan: Plan, trial: str, reason: str) -> str | None:
    specs = {s.id: s for s in plan.specs}
    if trial not in specs:
        return f"plan {plan.name} has no trial {trial}"
    state = State(root, plan)
    st = state.trial(specs[trial], [])
    if st["exported"]:
        return f"trial {trial} is exported; only a held or kept-local trial can be reopened"
    if st["reopened"]:
        return f"trial {trial} was reopened before"
    if not (st["held"] or st["kept_local"]):
        return f"trial {trial} is not held or kept local"
    runs = [e["run_id"] for e in state.events() if e.get("trial") == trial and "run_id" in e]
    state.add("trial-reopened", trial=trial, run_id=runs[-1] if runs else None, reason=reason)
    return None


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


def preflight(
    root: Path, plan: Plan, cap: float, checks: Checks, spec: TrialSpec | None = None
) -> list[str]:
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
    pairs = sorted({(s.variant, s.prompt_hash) for s in plan.specs if s.kind == "agent"})
    for variant, wanted in pairs:
        current = freeze.prompt_hash(root, variant)
        recorded = freeze.recorded_hash(root, variant)
        if not (current == recorded == wanted):
            problems.append(
                f"{variant} prompt hash {current} does not match the plan's {wanted} "
                f"and the recorded {recorded}"
            )
    pin = read_pin(Path(root) / "oversold.lock")[1]
    if plan.oversold_pin != pin:
        problems.append(f"the plan's Oversold pin {plan.oversold_pin} is not oversold.lock's {pin}")
    free = checks.mac_free_bytes(root)
    if free < MIN_FREE_BYTES:
        problems.append(f"the Mac has {fmt_bytes(free)} free, 5 GB needed")
    records = ledger.load(score.ledger_path_for(root))
    paid = plan.model != "scripted" and (spec is None or spec.kind == "agent")
    need = MIN_ROOM if paid else 0.0
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
    try:
        whole = json.dumps(json.loads(text), ensure_ascii=False, indent=0)
    except (json.JSONDecodeError, ValueError):
        whole = None
    out = [whole] if whole is not None else []
    for raw in [] if whole is not None else text.splitlines():
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


def allow_entries(root: Path) -> list[dict]:
    path = Path(root) / ALLOW_FILE
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def model_texts(folder: Path) -> list[str]:
    path = folder / "transcript.jsonl.gz"
    if not path.exists():
        return []
    out = []
    for line in gzip.decompress(path.read_bytes()).decode("utf-8").splitlines():
        event = json.loads(line)
        if event.get("event") == "reply":
            out += list(strings(event["message"]))
    return out


def enterprise_quotes(folder: Path, paths: tuple[str, ...]) -> list[str]:
    path = folder / "transcript.jsonl.gz"
    if not path.exists() or not paths:
        return []
    found = []
    for line in gzip.decompress(path.read_bytes()).decode("utf-8").splitlines():
        event = json.loads(line)
        if event.get("event") != "tool":
            continue
        for row in event["content"].splitlines():
            for p in paths:
                quoted = (
                    row.startswith(p) if p.endswith("/") else row.startswith((p + ":", p + ","))
                )
                if quoted and "this file is not available" not in row:
                    found.append(f"{ENTERPRISE}transcript.jsonl.gz: quotes {p}")
    return sorted(set(found))


def sentence_at(text: str, start: int, end: int) -> str:
    dot = text.rfind(". ", 0, start)
    value = text.rfind('": "', 0, start)
    left = max(
        dot + 2 if dot >= 0 else 0,
        value + 4 if value >= 0 else 0,
        text.rfind("\n", 0, start) + 1,
    )
    stops = [i for i in (text.find(". ", end), text.find("\n", end)) if i >= 0]
    right = min(stops) + 1 if stops else len(text)
    return text[left:right].strip()


def allowed(entries: list[dict], where: str, flat: str, start: int, end: int) -> bool:
    for entry in entries:
        if entry.get("path") != where:
            continue
        sentence = entry.get("sentence") or ""
        at = flat.find(sentence)
        while sentence and at >= 0:
            if at <= start and end <= at + len(sentence):
                return True
            at = flat.find(sentence, at + 1)
    return False


def word_file_rules(root: Path) -> list[dict]:
    path = Path(root) / WORD_FILES
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def file_rule_allows(rules: list[dict], word: str, where: str) -> bool:
    name = Path(where).name
    return any(
        r.get("word") == word
        and where.startswith(r.get("under", ""))
        and name in r.get("files", [])
        for r in rules
    )


def scan_export(
    root: Path,
    folder: Path,
    quotes: Quotes,
    key: str | None,
    words: list[str] | None,
    allow: list[dict] | None = None,
    file_rules: list[dict] | None = None,
    allowed_out: list[dict] | None = None,
) -> list[str]:
    problems = []
    if words is None:
        problems.append(f"no private word list at {WORDS_FILE}")
    model = model_texts(folder)
    problems += enterprise_quotes(folder, agent.enterprise_paths(root))
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
        where = score.relative(root, path)
        for word in words or []:
            for m in re.finditer(re.escape(word), low):
                if quotes.quoted(flat, m.start(), m.end(), word):
                    continue
                if allowed(allow or [], where, flat, m.start(), m.end()):
                    continue
                if file_rule_allows(file_rules or [], word, where):
                    if allowed_out is not None:
                        sentence = sentence_at(flat, m.start(), m.end())
                        allowed_out.append({"path": where, "word": word, "sentence": sentence})
                    continue
                left = flat[max(0, m.start() - QUOTE_WINDOW) : m.end()]
                right = flat[m.start() : m.end() + QUOTE_WINDOW]
                if any(left in t or right in t for t in model):
                    sentence = sentence_at(flat, m.start(), m.end())
                    problems.append(f"{MODEL_TEXT}{rel}: {word!r} in: {sentence}")
                else:
                    problems.append(f"{rel}: {word!r} that is not a quote of Medusa or a report")
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


def export_baseline(
    root: Path, run_id: str, dest: Path, records: list[dict], exporter: Callable[[str, Path], None]
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
    trial = next(r for r in records if r.get("kind") == "trial")
    (dest / "candidates").mkdir()
    for name in trial["candidate_names"]:
        shutil.copy(root / "runs" / "sweep" / run_id / f"{name}.yaml", dest / "candidates")
    paths = [dest / "candidates" / f"{n}.yaml" for n in trial["candidate_names"]]
    if score.candidate_list_sha256(paths) != trial["candidates_sha256"]:
        raise RuntimeError("the exported candidate list does not match its sha256")
    with (dest / "ledger.jsonl").open("w", encoding="ascii") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")
    cases = score.load_cases(root / "benchmark" / "cases")
    return score.trial_summary(records, {c: cases[c].rule for c in cases})


def baseline_manual_checks(records: list[dict]) -> list[str]:
    return [n for r in records if r.get("kind") == "final" for n in r.get("manual_check") or []]


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
        self.key = None
        env = self.root / ".env"
        if env.exists() and plan.model != "scripted":
            from shortfall.models import load_key

            self.key = load_key(env)
        self.words = private_words(self.root)
        self.last_allowed: list[dict] = []
        self.scanner = scanner or self.scan
        self.sweep_command = [sys.executable, "-u", "-m", "shortfall.sweep"]

    def scan(self, folder: Path) -> list[str]:
        self.last_allowed = []
        return scan_export(
            self.root,
            folder,
            self.quotes,
            self.key,
            self.words,
            allow_entries(self.root),
            word_file_rules(self.root),
            self.last_allowed,
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

    def dest(self, spec: TrialSpec) -> Path:
        if spec.kind == "baseline":
            return self.plan.baseline_root / spec.id
        return self.plan.export_root / spec.id

    def run(self) -> int:
        self.state.add("plan-start", plan=self.plan.name, dollar_cap=self.cap)
        for spec in trial_order(self.plan):
            records = self.records()
            st = self.state.trial(spec, records)
            if st["exported"] or st["held"] or st["kept_local"]:
                continue
            if st["finished"]:
                if spec.kind == "baseline":
                    outcome = self.finish_baseline(spec, st["finished"][-1], records)
                else:
                    outcome = self.finish(spec, st["finished"][-1], records, False)
                if outcome:
                    return outcome
                continue
            for run_id in st["unfinished"]:
                if run_id not in st["logged_interrupted"]:
                    self.state.add("trial-interrupted", trial=spec.id, run_id=run_id)
            if len(st["unfinished"]) + st["reopened"] >= 2:
                return self.stop(f"trial {spec.id} was interrupted twice")
            if self.state.pause_path.exists():
                self.state.add("plan-paused", before=spec.id)
                return 0
            problems = preflight(self.root, self.plan, self.cap, self.checks, spec)
            if problems:
                return self.stop("; ".join(problems))
            if spec.kind == "baseline":
                outcome = self.run_baseline(spec)
            else:
                room = rooms(records, self.state.run_ids(), self.cap)["plan"]
                dollars = min(self.plan.caps.dollars, room)
                outcome = self.run_trial(spec, dollars, dollars < self.plan.caps.dollars)
            if outcome:
                return outcome
        self.state.add("plan-done", plan=self.plan.name)
        return self.review_held()

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
            task_mode=spec.mode,
            feedback=spec.cell.feedback,
            issue=issue_stem(self.root, spec.cell.issue),
            caps=caps,
            image=self.oversold.image(agent.VERSION),
            pin=self.oversold.pin,
            validate=self.validate,
            variant=spec.variant,
        )
        end = trial.run()
        self.state.add("trial-end", trial=spec.id, run_id=run_id, reason=end["reason"])
        return self.finish(spec, run_id, self.records(), lowered)

    def run_baseline(self, spec: TrialSpec) -> int:
        cmd = [*self.sweep_command, "--mode", spec.method]
        cmd += ["--max-runs", str(self.plan.baseline_runs)]
        flag = "--order-seed" if spec.method == "grid" else "--seed"
        cmd += [flag, str(spec.number)]
        log = self.state.folder / f"{spec.id}.log"
        proc = subprocess.Popen(
            cmd, cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        run_id = None
        with log.open("a", encoding="utf-8") as f:
            for line in proc.stdout:
                f.write(line)
                f.flush()
                found = re.search(r"to runs/sweep/(\S+?), list sha256", line)
                if run_id is None and found:
                    run_id = found.group(1)
                    self.state.add("trial-start", trial=spec.id, run_id=run_id, kind="baseline")
        code = proc.wait()
        if run_id is None:
            return self.stop(f"trial {spec.id}: the sweep did not start, exit {code}")
        self.state.add("trial-end", trial=spec.id, run_id=run_id, exit=code)
        if code != 0:
            reason = f"sweep exit {code}" + (", uncovered failure" if code == 3 else "")
            self.state.add("trial-kept-local", trial=spec.id, run_id=run_id, reason=reason)
            return self.stop(f"trial {spec.id}: {reason}")
        return self.finish_baseline(spec, run_id, self.records())

    def finish_baseline(self, spec: TrialSpec, run_id: str, records: list[dict]) -> int:
        mine = [r for r in records if r["attempt_id"].startswith(f"{run_id}-")]
        notes = baseline_manual_checks(mine)
        if notes:
            self.state.add("trial-held", trial=spec.id, run_id=run_id, notes=notes)
            return 0
        return self.export_and_record(spec, run_id, mine, None)

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
        return self.export_and_record(spec, run_id, mine, stop)

    def check_export(self, dest: Path) -> list[str]:
        bad = []
        folders = sorted(p.parent for p in dest.rglob("report.json"))
        for folder in folders:
            ok, text = self.verifier(folder)
            if not ok:
                bad.append(f"verify {folder.name}: {text.strip()[-120:]}")
        return bad + self.scanner(dest)

    def export_and_record(
        self,
        spec: TrialSpec,
        run_id: str,
        mine: list[dict],
        stop: str | None,
        review: list[dict] | None = None,
    ) -> int:
        dest = self.dest(spec)
        try:
            if spec.kind == "baseline":
                export_baseline(self.root, run_id, dest, mine, self.exporter)
            else:
                export_trial(self.root, run_id, dest, mine, self.exporter)
            if review:
                self.write_review(spec, dest, run_id, review)
            bad = self.check_export(dest)
        except (RuntimeError, OSError) as err:
            bad = [f"export: {err}"]
        held = [b for b in bad if b.startswith(HOLDS)]
        if bad and len(held) == len(bad):
            shutil.rmtree(dest, ignore_errors=True)
            self.state.add("trial-held", trial=spec.id, run_id=run_id, notes=held)
            return self.stop(stop) if stop else 0
        if bad:
            shutil.rmtree(dest, ignore_errors=True)
            self.state.add("trial-export-failed", trial=spec.id, run_id=run_id, problems=bad)
            return self.stop(f"trial {spec.id} failed its export checks: {bad[0]}")
        if spec.kind == "agent":
            name = freeze.HASH_FILES[spec.variant]
            copy = self.plan.export_root / name.name
            if not copy.exists():
                shutil.copy(self.root / name, copy)
        fields = {"trial": spec.id, "run_id": run_id, "folder": score.relative(self.root, dest)}
        if self.last_allowed:
            fields["allowed_words"] = list(self.last_allowed)
        if review:
            fields["note"] = "published after review"
        self.state.add("trial-exported", **fields)
        return self.stop(stop) if stop else 0

    def review_attempt(self, spec: TrialSpec, final: dict) -> dict:
        scenario = self.root / final["scenario"]
        text = scenario.read_text(encoding="utf-8")
        folder = self.root / "runs" / "review" / self.plan.name / spec.id
        folder.mkdir(parents=True, exist_ok=True)
        builds = {
            "plain": (scenario.stem, text),
            REVIEW_FIX: (
                f"{scenario.stem}-{REVIEW_FIX}-control",
                control.variant(text, REVIEW_FIX, agent.VERSION),
            ),
            "redis": (f"{scenario.stem}-redis-control", control.redis_locking(text)),
        }
        out = {"attempt_id": final["attempt_id"], "scenario": final["scenario"], "sets": {}}
        for label, (stem, body) in builds.items():
            path = folder / f"{stem}.yaml"
            path.write_text(body, encoding="utf-8")
            result = self.oversold.run(path, REVIEW_RUNS, agent.VERSION)
            c = score.counts(result.histories)
            out["sets"][label] = {
                "folder": result.folder,
                "runs": len(result.histories),
                "fails": {rule: row["fail"] for rule, row in c.items()},
                "inconclusive": score.inconclusive_runs(result.histories),
            }
        return out

    def write_review(self, spec: TrialSpec, dest: Path, run_id: str, review: list[dict]) -> None:
        folder = dest / "review"
        folder.mkdir()
        for item in review:
            for data in item["sets"].values():
                self.exporter(data["folder"], folder / Path(data["folder"]).name)
        write_json(
            folder / "review.json",
            {
                "trial": spec.id,
                "run_id": run_id,
                "label": review[0].get("label", "covered by #17032, rare in this scenario"),
                "note": "These runs were made after the trial, only to decide whether to "
                "publish it. They do not change the trial's score or its runs to first "
                "reproduction.",
                "attempts": [
                    {
                        **item,
                        "sets": {
                            k: {**v, "folder": Path(v["folder"]).name}
                            for k, v in item["sets"].items()
                        },
                    }
                    for item in review
                ],
            },
        )

    def review_held(self) -> int:
        events = self.state.events()
        closed = {
            e["trial"]
            for e in events
            if e["event"] in ("trial-exported", "review-kept-held", "review-stop")
        }
        specs = {s.id: s for s in self.plan.specs}
        for e in events:
            if e["event"] != "trial-held" or e["trial"] in closed or e["trial"] not in specs:
                continue
            notes = e.get("notes") or []
            if not notes or any(str(n).startswith(HOLDS) for n in notes):
                continue
            spec, run_id = specs[e["trial"]], e["run_id"]
            mine = [r for r in self.records() if r["attempt_id"].startswith(f"{run_id}-")]
            finals = [r for r in mine if r.get("kind") == "final" and r.get("manual_check")]
            review = []
            for final in finals:
                rules = sorted({n.split(" ")[0] for n in final["manual_check"]})
                item = self.review_attempt(spec, final)
                item["rules"] = rules
                fixed = [
                    f"{label} {rule} {n}"
                    for label in (REVIEW_FIX, "redis")
                    for rule, n in item["sets"][label]["fails"].items()
                    if n
                ]
                if fixed:
                    self.state.add("review-stop", trial=spec.id, run_id=run_id, failures=fixed)
                    return self.stop(
                        f"review of {spec.id}: a check failed on a fix build or with Redis"
                    )
                item["plain_hits"] = all(item["sets"]["plain"]["fails"].get(r, 0) for r in rules)
                review.append(item)
            if review and all(item["plain_hits"] for item in review):
                outcome = self.export_and_record(spec, run_id, mine, None, review)
                if outcome:
                    return outcome
            else:
                self.state.add("review-kept-held", trial=spec.id, run_id=run_id, review=review)
        return 0


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
    stops = [e for e in events if e["event"] in ("plan-stop", "plan-done", "plan-paused")]
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
        "pause_file": state.pause_path.exists(),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.trials")
    p.add_argument("plan")
    p.add_argument("--status", action="store_true")
    p.add_argument("--review", action="store_true", help="only review held trials")
    p.add_argument("--raise-dollar-cap", type=float, default=0.0)
    p.add_argument("--reopen", metavar="TRIAL", help="rerun a held or kept-local trial")
    p.add_argument("--reason", default="")
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    plan = load_plan(root, Path(args.plan))
    if args.status:
        print(json.dumps(status(root, plan), indent=1))
        return 0
    if args.reopen:
        if not args.reason:
            print("--reopen needs --reason")
            return 1
        problem = reopen(root, plan, args.reopen, args.reason)
        print(problem or f"trial {args.reopen} reopened; it runs from scratch on the next run")
        return 1 if problem else 0
    state = State(root, plan)
    if state.pid_path.exists():
        text = state.pid_path.read_text().strip()
        pid = int(text) if text.isdigit() else 0
        if pid and pid not in (os.getpid(), os.getppid()) and pid_alive(pid):
            print(f"plan {plan.name} is already running as process {pid}")
            return 1
    os.setpgrp()
    runner = Runner(root, plan, args.raise_dollar_cap)
    return runner.review_held() if args.review else runner.run()


if __name__ == "__main__":
    sys.exit(main())
