import datetime
import hashlib
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml

from shortfall import ledger
from shortfall.budget import ATTEMPT, Budget, CapReached, from_flags
from shortfall.cases import RULES, load_case
from shortfall.control import one_server
from shortfall.coverage import covering_issues
from shortfall.pin import read_pin
from shortfall.sweep import SKUS

SCREEN_RUNS = 3
HARNESS_STREAK = 3
SCORE_RUNS = 10
CONTROL_RUNS = 10
RESULTS = ("fail", "pass", "inconclusive")


@dataclass
class RunSet:
    folder: str
    histories: list[dict]


class Runner(Protocol):
    def run(self, scenario: Path, runs: int, version: str) -> RunSet: ...


class UncoveredFailure(Exception):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def relative(root: Path, path: Path) -> str:
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def clean(text: str, root: Path) -> str:
    text = text.replace(str(Path(root).resolve()), ".").replace(str(root), ".")
    home = os.path.expanduser("~")
    if home and home not in ("~", "/"):
        text = text.replace(home, "~")
    return text


def shape(data: dict) -> dict:
    groups = []
    carts = 0
    several = False
    for cart in data["carts"].values():
        count = cart.get("count", 1)
        carts += count
        items = [SKUS[line["sku"]][0] for line in cart["lines"]]
        if len(items) != len(set(items)):
            several = True
        groups.append(
            {
                "server": cart["server"],
                "count": count,
                "lines": [f"{line['sku']} {line['qty']}" for line in cart["lines"]],
            }
        )
    return {
        "servers": data["target"]["servers"],
        "carts": carts,
        "groups": groups,
        "stock": dict(data.get("stock") or {}),
        "release": data["timing"]["release"],
        "item_on_several_lines": several,
    }


def counts(histories: list[dict]) -> dict[str, dict[str, int]]:
    c = {rule: dict.fromkeys(RESULTS, 0) for rule in RULES}
    for history in histories:
        for verdict in history.get("verdicts") or []:
            if verdict["check"] in c and verdict["result"] in RESULTS:
                c[verdict["check"]][verdict["result"]] += 1
    return c


def fails(c: dict) -> dict[str, int]:
    return {rule: c[rule]["fail"] for rule in RULES}


def failed_rules(c: dict) -> list[str]:
    return [rule for rule in RULES if c[rule]["fail"] > 0]


def inconclusive_runs(histories: list[dict]) -> int:
    return sum(
        1
        for h in histories
        if any(v["result"] == "inconclusive" for v in (h.get("verdicts") or []))
        or not h.get("verdicts")
    )


def case_map(cases_root: Path) -> dict[tuple[str, int], str]:
    mapping: dict[tuple[str, int], str] = {}
    for folder in sorted(p for p in Path(cases_root).iterdir() if p.is_dir()):
        case = load_case(folder)
        ref = yaml.safe_load((folder / case.reference.file).read_text(encoding="utf-8"))
        key = (case.rule, ref["target"]["servers"])
        if key in mapping:
            raise ValueError(f"cases {mapping[key]} and {case.id} share rule and server count")
        mapping[key] = case.id
    return mapping


class OversoldRunner:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.pin = read_pin(self.root / "oversold.lock")[1]
        self.image_id: str | None = None

    def _wrapper(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sh", "scripts/oversold.sh", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def image(self, version: str) -> tuple[str, str]:
        proc = self._wrapper("image", version)
        found = re.search(r" id (sha256:[0-9a-f]{64}) digest (\S+)", proc.stdout)
        if proc.returncode != 0 or not found:
            raise RuntimeError(clean(proc.stderr.strip() or "image lookup failed", self.root))
        self.image_id = found.group(1)
        return found.group(1), found.group(2)

    def run(self, scenario: Path, runs: int, version: str) -> RunSet:
        proc = self._wrapper("run", str(scenario), "--runs", str(runs), "--version", version)
        if proc.returncode not in (0, 1, 3):
            tail = (proc.stderr.strip() or proc.stdout.strip()).splitlines()[-3:]
            raise RuntimeError(clean(f"oversold run exited {proc.returncode}: {tail}", self.root))
        found = re.findall(r"report (\S+)/report\.json", proc.stdout)
        if not found:
            raise RuntimeError("oversold run printed no report path")
        folder = Path(found[-1])
        histories = [
            json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("run-*.json"))
        ]
        if len(histories) != runs:
            raise RuntimeError(f"expected {runs} histories, found {len(histories)}")
        for h in histories:
            if h.get("oversold") != {"commit": self.pin, "dirty": False}:
                raise RuntimeError("a history does not record the pinned Oversold commit")
            ids = {s.get("image_id") for s in ((h.get("target") or {}).get("servers") or [])}
            if ids and self.image_id and ids != {self.image_id}:
                raise RuntimeError(f"a history ran on image {sorted(ids)}, not {self.image_id}")
        return RunSet(folder=relative(self.root, folder), histories=histories)


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def score_candidate(
    root: Path,
    scenario: Path,
    version: str,
    runner: Runner,
    budget: Budget,
    cases: dict[tuple[str, int], str],
    image_id: str,
    image_digest: str,
    pin: str,
    meta: dict,
) -> tuple[dict, str | None]:
    text = scenario.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    sh = shape(data)
    entry = dict(meta)
    entry.update(
        scenario=relative(root, scenario),
        scenario_sha256=sha256_text(text),
        case=None,
        cases=[],
        medusa_version=version,
        carts=sh["carts"],
        servers=sh["servers"],
        shape=sh,
        screen_runs=0,
        score_runs=0,
        control_runs=0,
        candidate_fails={"screen": None, "score": None},
        control_fails=None,
        inconclusive={"screen": 0, "score": 0, "control": 0},
        rules_failed=[],
        verdict="inconclusive",
        oversold_commit=pin,
        medusa_image_id=image_id,
        medusa_image_digest=image_digest,
        run_folders=[],
        stop_reason=None,
    )
    budget.start_attempt()
    start = time.monotonic()
    stop = None

    def run_set(name: str, path: Path, runs: int, set_shape: dict) -> dict:
        budget.charge_runs(runs)
        result = runner.run(path, runs, version)
        entry["run_folders"].append(result.folder)
        c = counts(result.histories)
        entry["inconclusive"][name] = inconclusive_runs(result.histories)
        if name == "control":
            entry["control_runs"] = runs
            entry["control_fails"] = fails(c)
        else:
            entry[f"{name}_runs"] = runs
            entry["candidate_fails"][name] = fails(c)
            entry["rules_failed"] = sorted(
                set(entry["rules_failed"]) | set(failed_rules(c)), key=RULES.index
            )
        for rule in failed_rules(c):
            if not covering_issues(set_shape, rule):
                raise UncoveredFailure(
                    f"uncovered failure: {rule} failed {c[rule]['fail']} of {runs} runs in the "
                    f"{name} set, and no issue in the coverage map covers this shape"
                )
        return c

    def decide() -> str:
        screen = run_set("screen", scenario, SCREEN_RUNS, sh)
        if not failed_rules(screen):
            return "inconclusive" if entry["inconclusive"]["screen"] else "no match"
        scored = run_set("score", scenario, SCORE_RUNS, sh)
        score_rules = failed_rules(scored)
        if sh["servers"] == 1:
            hits = [cases[(r, 1)] for r in score_rules if (r, 1) in cases]
            entry["cases"] = hits
            entry["case"] = hits[0] if hits else None
            if score_rules:
                return "reproduction only"
            return "inconclusive" if entry["inconclusive"]["score"] else "no match"
        candidate_rules = [r for r in score_rules if (r, 2) in cases]
        if not candidate_rules:
            if not score_rules and entry["inconclusive"]["score"]:
                return "inconclusive"
            return "no match"
        control_text = one_server(text)
        control_path = scenario.with_name(f"{scenario.stem}-control.yaml")
        if control_path.exists() and control_path.read_text(encoding="utf-8") != control_text:
            raise RuntimeError(f"{control_path.name} exists and differs from the generated control")
        control_path.write_text(control_text, encoding="utf-8")
        control = run_set(
            "control", control_path, CONTROL_RUNS, shape(yaml.safe_load(control_text))
        )
        clean_control = entry["inconclusive"]["control"] == 0
        matched = [r for r in candidate_rules if control[r]["fail"] == 0 and clean_control]
        if matched:
            entry["cases"] = [cases[(r, 2)] for r in matched]
            entry["case"] = entry["cases"][0]
            return "match"
        if not clean_control and any(control[r]["fail"] == 0 for r in candidate_rules):
            return "inconclusive"
        return "no match"

    try:
        entry["verdict"] = decide()
    except CapReached as err:
        entry["stop_reason"] = str(err)
        stop = None if err.cap == ATTEMPT else str(err)
    except UncoveredFailure as err:
        entry["stop_reason"] = str(err)
        stop = str(err)
    except RuntimeError as err:
        entry["stop_reason"] = clean(f"error: {err}", root)
        stop = entry["stop_reason"]
    entry["wall_seconds"] = round(time.monotonic() - start, 1)
    entry["oversold_runs"] = budget.attempt_used
    entry["timestamp"] = now()
    return entry, stop


def _fails_text(f: dict | None) -> str:
    if not f:
        return "-"
    return ",".join(f"{rule}={n}" for rule, n in f.items() if n) or "none"


def describe_entry(entry: dict) -> str:
    return (
        f"{entry['attempt_id']} {Path(entry['scenario']).stem}: {entry['verdict']}"
        f"{' ' + entry['case'] if entry['case'] else ''} | runs {entry['oversold_runs']} | "
        f"screen {_fails_text(entry['candidate_fails']['screen'])} | "
        f"score {_fails_text(entry['candidate_fails']['score'])} | "
        f"control {_fails_text(entry['control_fails'])}"
        f"{' | stop: ' + entry['stop_reason'] if entry['stop_reason'] else ''}"
    )


def _start(root: Path, version: str, max_runs, raise_dollar_cap):
    budget = from_flags(max_runs, raise_dollar_cap)
    runner = OversoldRunner(root)
    image_id, digest = runner.image(version)
    print(f"sweep: medusa {version} image {image_id} digest {digest}")
    cases = case_map(Path(root) / "benchmark" / "cases")
    return budget, runner, image_id, digest, cases


def only_inconclusive(entry: dict) -> bool:
    used = entry["screen_runs"] + entry["score_runs"] + entry["control_runs"]
    return used > 0 and sum(entry["inconclusive"].values()) == used


def run_sweep(
    root: Path,
    paths: list[Path],
    version: str,
    seed: int,
    stamp: str,
    max_runs=None,
    raise_dollar_cap=None,
) -> int:
    try:
        budget, runner, image_id, digest, cases = _start(root, version, max_runs, raise_dollar_cap)
    except RuntimeError as err:
        print(f"sweep: {err}")
        return 2
    ledger_path = Path(root) / "runs" / "ledger.jsonl"
    entries = []
    stop = None
    streak = 0
    for index, path in enumerate(paths, start=1):
        if budget.session_left() < SCREEN_RUNS:
            stop = (
                f"session runs cap: {budget.session_left()} runs left, a screen needs {SCREEN_RUNS}"
            )
            break
        meta = {
            "attempt_id": f"{stamp}-{index:03d}",
            "source": "sweep",
            "seed": seed,
            "rerun_of": None,
        }
        entry, stop = score_candidate(
            root, path, version, runner, budget, cases, image_id, digest, runner.pin, meta
        )
        ledger.append(ledger_path, entry)
        entries.append(entry)
        print(describe_entry(entry), flush=True)
        if stop:
            break
        streak = streak + 1 if only_inconclusive(entry) else 0
        if streak >= HARNESS_STREAK:
            stop = f"harness: {streak} attempts in a row had only inconclusive runs"
            break
    screened = sum(1 for e in entries if e["screen_runs"])
    scored = sum(1 for e in entries if e["score_runs"])
    print(
        f"sweep: {len(paths)} candidates, {len(entries)} attempted, {screened} screened, "
        f"{scored} scored, {len(paths) - len(entries)} skipped"
    )
    if stop:
        print(f"sweep: stopped: {stop}")
    print(json.dumps(ledger.summary(entries), indent=2))
    print(budget.describe())
    if stop and stop.startswith("uncovered"):
        return 3
    return 0


def rerun(root: Path, attempt_id: str, stamp: str, max_runs=None, raise_dollar_cap=None) -> int:
    ledger_path = Path(root) / "runs" / "ledger.jsonl"
    old = ledger.find(ledger.load(ledger_path), attempt_id)
    path = Path(root) / old["scenario"]
    if sha256_text(path.read_text(encoding="utf-8")) != old["scenario_sha256"]:
        print(f"rerun: {old['scenario']} changed since attempt {attempt_id}")
        return 2
    try:
        budget, runner, image_id, digest, cases = _start(
            root, old["medusa_version"], max_runs, raise_dollar_cap
        )
    except RuntimeError as err:
        print(f"rerun: {err}")
        return 2
    if image_id != old["medusa_image_id"]:
        print(f"rerun: image {image_id} differs from {old['medusa_image_id']}, not comparable")
        return 2
    meta = {
        "attempt_id": f"{stamp}-rerun",
        "source": "sweep",
        "seed": old["seed"],
        "rerun_of": attempt_id,
    }
    entry, stop = score_candidate(
        root, path, old["medusa_version"], runner, budget, cases, image_id, digest, runner.pin, meta
    )
    ledger.append(ledger_path, entry)
    print(describe_entry(entry))
    same = entry["verdict"] == old["verdict"] and entry["case"] == old["case"]
    print(f"rerun: before {old['verdict']} {old['case']}, now {entry['verdict']} {entry['case']}")
    print(f"rerun: same verdict: {'yes' if same else 'no'}")
    print(budget.describe())
    if stop:
        print(f"rerun: stopped: {stop}")
    return 0 if same else 1
