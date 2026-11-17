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
from shortfall.answers import located
from shortfall.budget import ATTEMPT, Budget, CapReached, from_flags
from shortfall.cases import RULES, Control, load_case
from shortfall.control import one_server, redis_locking, variant
from shortfall.coverage import MANUAL_CHECK, covering_issues
from shortfall.pin import read_pin
from shortfall.scenario_format import unknown_fields
from shortfall.spend import Meter, now
from shortfall.sweep import SKUS

SCREEN_RUNS = 3
RETRY_RUNS = 7
HARNESS_STREAK = 3
SETUP_ERROR = "prepare cart "
LOCK_ERROR = "redis locking: "
IMAGE_ERROR = re.compile(
    r"image inputs|oversold\.image-inputs|that variant \S+ lists|variant \S+ replaces"
)
SCORE_RUNS = 10
CONTROL_RUNS = 10
RESULTS = ("fail", "pass", "inconclusive")
VIOLATION = "violation"
UNPREPARABLE = "unpreparable"
INCONCLUSIVE = "inconclusive"
REPRODUCED = "reproduced"
NOT_REPRODUCED = "not reproduced"
NOT_ISOLATED = "violation, cause not isolated"
CUT_OFF = "cut off by the run cap"
HARNESS_ONLY = ("target.variant", "target.locking")
CONTROLS = {
    "one-server": ("control", one_server),
    "redis-locking": ("redis-control", redis_locking),
}


def control_builder(control: Control | None, version: str):
    if control is None:
        return None
    if control.kind in CONTROLS:
        return CONTROLS[control.kind]
    if control.kind == "variant" and control.version == version:

        def build(text: str) -> str:
            return variant(text, control.variant, control.version)

        return f"{control.variant}-control", build
    return None


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
        "locking": data["target"].get("locking", "in-memory"),
        "variant": data["target"].get("variant"),
    }


def harness_error(history: dict, prefix: str) -> str | None:
    error = history.get("harness_error")
    if isinstance(error, str) and error.startswith(prefix):
        return error
    for verdict in history.get("verdicts") or []:
        reason = verdict.get("reason") or ""
        if verdict.get("result") == "inconclusive" and reason.startswith(
            "harness error: " + prefix
        ):
            return reason.removeprefix("harness error: ")
    return None


def setup_error(history: dict) -> str | None:
    return harness_error(history, SETUP_ERROR)


def lock_error(history: dict) -> str | None:
    return harness_error(history, LOCK_ERROR)


def image_error(history: dict) -> str | None:
    texts = [history.get("harness_error")]
    texts += [
        (v.get("reason") or "").removeprefix("harness error: ")
        for v in history.get("verdicts") or []
        if v.get("result") == "inconclusive"
        and (v.get("reason") or "").startswith("harness error: ")
    ]
    for text in texts:
        if isinstance(text, str) and IMAGE_ERROR.search(text):
            return text
    return None


def rule_order(rule: str) -> tuple[int, str]:
    return (RULES.index(rule) if rule in RULES else len(RULES), rule)


def unknown_completion(history: dict) -> bool:
    return any(
        op.get("step") == "complete_cart" and op.get("outcome") == "unknown"
        for op in history.get("operations") or []
    )


def counts(histories: list[dict]) -> dict[str, dict[str, int]]:
    c: dict[str, dict[str, int]] = {}
    for history in histories:
        unknown = unknown_completion(history)
        for verdict in history.get("verdicts") or []:
            row = c.setdefault(verdict["check"], dict.fromkeys(RESULTS, 0))
            result = "inconclusive" if unknown else verdict["result"]
            if result in RESULTS:
                row[result] += 1
    return {rule: c[rule] for rule in sorted(c, key=rule_order)}


def check_versions(histories: list[dict]) -> dict[str, list[int]]:
    seen: dict[str, set[int]] = {}
    for history in histories:
        for verdict in history.get("verdicts") or []:
            seen.setdefault(verdict["check"], set()).add(verdict["version"])
    return {rule: sorted(seen[rule]) for rule in sorted(seen, key=rule_order)}


def merge_versions(a: dict[str, list[int]], b: dict[str, list[int]]) -> dict[str, list[int]]:
    out = {rule: set(v) for rule, v in a.items()}
    for rule, v in b.items():
        out.setdefault(rule, set()).update(v)
    return {rule: sorted(out[rule]) for rule in sorted(out, key=rule_order)}


def fails(c: dict) -> dict[str, int]:
    return {rule: row["fail"] for rule, row in c.items()}


def failed_rules(c: dict) -> list[str]:
    return [rule for rule, row in c.items() if row["fail"] > 0]


def inconclusive_runs(histories: list[dict]) -> int:
    return sum(
        1
        for h in histories
        if any(v["result"] == "inconclusive" for v in (h.get("verdicts") or []))
        or not h.get("verdicts")
        or unknown_completion(h)
    )


def not_reproduced_within(runs: int) -> str:
    return f"not reproduced within {runs} runs"


class CandidateRefused(ValueError):
    pass


def check_candidate(data) -> None:
    target = data.get("target") if isinstance(data, dict) else None
    if not isinstance(target, dict):
        raise CandidateRefused("a candidate needs a target mapping")
    if "checks" in data:
        raise CandidateRefused("a candidate may not set checks, every run uses every check")
    found = [f"target.{key}" for key in ("variant", "locking") if key in target]
    if found:
        raise CandidateRefused(
            f"a candidate may not set {' or '.join(found)}, only the harness sets them"
        )
    unknown = unknown_fields(data)
    if unknown:
        raise CandidateRefused(
            f"a candidate may not set {', '.join(unknown)}: not a field of the scenario format"
        )


@dataclass(frozen=True)
class CaseInfo:
    id: str
    rule: str
    folder: Path
    scoring: Control


def load_cases(cases_root: Path) -> dict[str, CaseInfo]:
    out = {}
    for folder in sorted(p for p in Path(cases_root).iterdir() if p.is_dir()):
        case = load_case(folder)
        out[case.id] = CaseInfo(id=case.id, rule=case.rule, folder=folder, scoring=case.scoring)
    return out


def control_key(control: Control) -> tuple:
    return (control.kind, control.variant, control.version)


def check_histories(histories: list[dict], runs: int, pin: str, image_id: str | None) -> None:
    if len(histories) != runs:
        raise RuntimeError(f"expected {runs} histories, found {len(histories)}")
    for h in histories:
        if h.get("oversold") != {"commit": pin, "dirty": False}:
            raise RuntimeError("a history does not record the pinned Oversold commit")
        target = h.get("target") or {}
        servers = target.get("servers") or []
        ids = {s.get("image_id") for s in servers}
        if ids and image_id and ids != {image_id}:
            raise RuntimeError(f"a history ran on image {sorted(ids)}, not {image_id}")
        if "image_inputs" in target:
            labels = {s.get("image_inputs") for s in servers}
            if labels != {target["image_inputs"]}:
                raise RuntimeError(
                    f"a history's servers have image inputs {sorted(map(str, labels))}, "
                    f"not {target['image_inputs']}"
                )
        variant = target.get("variant")
        if variant:
            want = {f["path"]: f["sha256"] for f in variant.get("files") or []}
            for s in servers:
                got = {f["path"]: f["sha256"] for f in s.get("variant_files") or []}
                if got != want:
                    raise RuntimeError(
                        f"{s.get('service')} has replaced files {got}, variant "
                        f"{variant.get('name')} lists {want}"
                    )


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

    def lookup(self, version: str, variant_name: str | None = None) -> tuple[str, str]:
        args = ["image", version] + ([variant_name] if variant_name else [])
        proc = self._wrapper(*args)
        found = re.search(r" id (sha256:[0-9a-f]{64}) digest (\S+)", proc.stdout)
        if proc.returncode != 0 or not found:
            raise RuntimeError(clean(proc.stderr.strip() or "image lookup failed", self.root))
        return found.group(1), found.group(2)

    def image(self, version: str) -> tuple[str, str]:
        image_id, digest = self.lookup(version)
        self.image_id = image_id
        return image_id, digest

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
        data = yaml.safe_load(Path(scenario).read_text(encoding="utf-8"))
        variant_name = (data.get("target") or {}).get("variant")
        expected = self.lookup(version, variant_name)[0] if variant_name else self.image_id
        check_histories(histories, runs, self.pin, expected)
        return RunSet(folder=relative(self.root, folder), histories=histories)


class Attempt:
    def __init__(
        self,
        root: Path,
        scenario: Path,
        version: str,
        runner: Runner,
        budget: Budget,
        cases: dict[str, CaseInfo],
        image_id: str,
        image_digest: str,
        pin: str,
        meta: dict,
        ledger_path: Path,
        named_file: str | None = None,
        named_cause: str | None = None,
    ):
        self.root = Path(root)
        self.scenario = Path(scenario)
        self.version = version
        self.runner = runner
        self.budget = budget
        self.cases = cases
        self.named_file = named_file
        self.named_cause = named_cause
        self.text = self.scenario.read_text(encoding="utf-8")
        data = yaml.safe_load(self.text)
        check_candidate(data)
        self.shape = shape(data)
        self.entry = dict(meta)
        self.entry.update(
            scenario=relative(self.root, self.scenario),
            scenario_sha256=sha256_text(self.text),
            medusa_version=version,
            carts=self.shape["carts"],
            servers=self.shape["servers"],
            shape=self.shape,
            screen_runs=0,
            retry_runs=0,
            score_runs=0,
            control_runs=0,
            candidate_fails={"screen": None, "retry": None, "score": None},
            controls=[],
            inconclusive={"screen": 0, "retry": 0, "score": 0, "control": 0},
            rules_failed=[],
            check_versions={},
            violation={"result": INCONCLUSIVE, "rules": {}, "runs": 0},
            reproduced={"cases": {}, "rules": {}},
            reproduced_at={},
            located={"result": "not applicable"},
            oversold_commit=pin,
            medusa_image_id=image_id,
            medusa_image_digest=image_digest,
            run_folders=[],
            stop_reason=None,
            setup_error=None,
            manual_check=[],
        )
        self.meter = Meter(ledger_path, budget, self.entry["attempt_id"])
        self.used = 0
        self.seconds = 0.0
        self.stop: str | None = None
        self.done = False
        self.finished = False
        self.histories: dict[str, list[dict]] = {"screen": [], "retry": [], "score": []}
        budget.start_attempt()
        self.meter.start(
            {
                "source": self.entry["source"],
                "seed": self.entry["seed"],
                "scenario": self.entry["scenario"],
                "scenario_sha256": self.entry["scenario_sha256"],
                "medusa_version": version,
                "medusa_image_id": image_id,
                "oversold_commit": pin,
                "rerun_of": self.entry.get("rerun_of"),
            }
        )

    def _run(self, name: str, path: Path, runs: int) -> list[dict]:
        self.meter.runs(name, runs)
        result = self.runner.run(path, runs, self.version)
        self.entry["run_folders"].append(result.folder)
        return result.histories

    def _record(self, name: str, histories: list[dict], set_shape: dict, label: str) -> dict:
        runs = len(histories)
        locks = [lock_error(h) for h in histories if lock_error(h)]
        if locks:
            raise RuntimeError(
                f"harness: {len(locks)} of {runs} runs in the {label} set made no lock calls "
                f"through Redis: {locks[0]}"
            )
        images = [image_error(h) for h in histories if image_error(h)]
        if images:
            raise RuntimeError(
                f"harness: {len(images)} of {runs} runs in the {label} set had an image or "
                f"variant file mismatch: {images[0]}"
            )
        c = counts(histories)
        entry = self.entry
        entry["check_versions"] = merge_versions(entry["check_versions"], check_versions(histories))
        if name in self.histories:
            entry[f"{name}_runs"] = runs
            entry["candidate_fails"][name] = fails(c)
            entry["inconclusive"][name] = inconclusive_runs(histories)
            entry["rules_failed"] = sorted(
                set(entry["rules_failed"]) | set(failed_rules(c)), key=rule_order
            )
        entry["manual_check"] = [
            n for n in entry["manual_check"] if f" in the {label} set," not in n
        ]
        for rule in failed_rules(c):
            issues = covering_issues(set_shape, rule)
            if not issues:
                raise UncoveredFailure(
                    f"uncovered failure: {rule} failed {c[rule]['fail']} of {runs} runs in the "
                    f"{label} set, and no issue in the coverage map covers this shape"
                )
            if set(issues) <= MANUAL_CHECK:
                entry["manual_check"].append(
                    f"{rule} failed {c[rule]['fail']} of {runs} runs in the {label} set, "
                    f"covered only by {', '.join(issues)}, which Oversold has never reproduced"
                )
        return c

    def _candidate_set(self, name: str, runs: int) -> bool:
        new = self._run(name, self.scenario, runs)
        self.histories[name] += new
        c = self._record(name, self.histories[name], self.shape, name)
        errors = [setup_error(h) for h in new if setup_error(h)]
        if errors:
            self.entry["setup_error"] = clean(errors[0], self.root)
            self.done = True
            return False
        return bool(failed_rules(c))

    def _guard(self, action) -> None:
        self.budget.attempt_used = self.used
        start = time.monotonic()
        try:
            action()
        except CapReached as err:
            self.entry["stop_reason"] = str(err)
            self.stop = None if err.cap == ATTEMPT else str(err)
            self.done = True
        except UncoveredFailure as err:
            self.entry["stop_reason"] = str(err)
            self.stop = str(err)
            self.done = True
        except RuntimeError as err:
            self.entry["stop_reason"] = clean(f"error: {err}", self.root)
            self.stop = self.entry["stop_reason"]
            self.done = True
        finally:
            self.used = self.budget.attempt_used
            self.seconds += time.monotonic() - start

    def first_pass(self) -> None:
        def action():
            self._candidate_set("screen", 1)
            if self.done:
                return
            if self._candidate_set("screen", SCREEN_RUNS - 1):
                self._score()

        self._guard(action)

    def second_pass(self) -> None:
        def action():
            if self._candidate_set("retry", RETRY_RUNS):
                self._score()
            self.done = True

        self._guard(action)

    def _score(self) -> None:
        self.done = True
        scored = self._candidate_set("score", SCORE_RUNS)
        if self.done and self.entry["setup_error"]:
            return
        score = counts(self.histories["score"])
        planned: dict[tuple, dict] = {}
        for rule in failed_rules(score) if scored else []:
            for case in sorted(self.cases.values(), key=lambda c: c.id):
                if case.rule != rule:
                    continue
                item = planned.setdefault(
                    control_key(case.scoring), {"control": case.scoring, "cases": []}
                )
                item["cases"].append(case.id)
        results = self.entry["reproduced"]["cases"]
        for item in planned.values():
            control = item["control"]
            built = control_builder(control, self.version)
            if built is None:
                for case_id in item["cases"]:
                    results[case_id] = f"no scoring control on {self.version}"
                continue
            suffix, build = built
            control_text = build(self.text)
            path = self.scenario.with_name(f"{self.scenario.stem}-{suffix}.yaml")
            if path.exists() and path.read_text(encoding="utf-8") != control_text:
                raise RuntimeError(f"{path.name} exists and differs from the generated control")
            path.write_text(control_text, encoding="utf-8")
            histories = self._run("control", path, CONTROL_RUNS)
            c = self._record("control", histories, shape(yaml.safe_load(control_text)), suffix)
            inconclusive = inconclusive_runs(histories)
            self.entry["controls"].append(
                {
                    "control": suffix,
                    "kind": control.kind,
                    "variant": control.variant,
                    "version": control.version,
                    "file": relative(self.root, path),
                    "cases": item["cases"],
                    "runs": len(histories),
                    "fails": fails(c),
                    "inconclusive": inconclusive,
                }
            )
            self.entry["control_runs"] += len(histories)
            self.entry["inconclusive"]["control"] += inconclusive
            for case_id in item["cases"]:
                rule = self.cases[case_id].rule
                cleared = c.get(rule, {"fail": 0})["fail"] == 0
                if cleared and inconclusive == 0:
                    results[case_id] = REPRODUCED
                    self.entry["reproduced_at"][case_id] = self.budget.session_used
                elif cleared:
                    results[case_id] = INCONCLUSIVE
                else:
                    results[case_id] = NOT_REPRODUCED
        self.entry["reproduced"]["cases"] = dict(sorted(results.items()))

    def finish(self) -> dict:
        if self.finished:
            return self.entry
        entry = self.entry
        runs = sum(len(h) for h in self.histories.values())
        totals: dict[str, int] = {}
        for name in self.histories:
            for rule, n in (entry["candidate_fails"][name] or {}).items():
                totals[rule] = totals.get(rule, 0) + n
        failed = {rule: n for rule, n in totals.items() if n}
        inconclusive = sum(entry["inconclusive"][n] for n in self.histories)
        if entry["setup_error"]:
            result = UNPREPARABLE
        elif failed:
            result = VIOLATION
        elif runs == 0 or inconclusive == runs:
            result = INCONCLUSIVE
        else:
            result = not_reproduced_within(runs)
        entry["violation"] = {"result": result, "rules": failed, "runs": runs}
        cases = dict(sorted(entry["reproduced"]["cases"].items()))
        entry["reproduced"]["cases"] = cases
        outcomes = {}
        for rule in sorted(failed, key=rule_order):
            mine = [cases.get(c.id) for c in self.cases.values() if c.rule == rule]
            if REPRODUCED in mine:
                outcomes[rule] = REPRODUCED
            elif INCONCLUSIVE in mine:
                outcomes[rule] = INCONCLUSIVE
            elif cut_off(entry, rule, {c.id: c.rule for c in self.cases.values()}):
                outcomes[rule] = CUT_OFF
            else:
                outcomes[rule] = NOT_ISOLATED
                note = (
                    f"{rule} failed {failed[rule]} of {runs} runs on plain Medusa {self.version}: "
                    f"{NOT_ISOLATED}, no case's scoring control clears it"
                )
                if note not in entry["manual_check"]:
                    entry["manual_check"].append(note)
        entry["reproduced"]["rules"] = outcomes
        hits = [case_id for case_id, r in cases.items() if r == REPRODUCED]
        folders = {case_id: info.folder for case_id, info in self.cases.items()}
        entry["located"] = located(folders, hits, self.named_file, self.named_cause)
        entry["wall_seconds"] = round(self.seconds, 1)
        entry["oversold_runs"] = self.used
        entry["timestamp"] = now()
        self.meter.finish(entry)
        self.finished = True
        return entry


def describe_entry(entry: dict) -> str:
    v = entry["violation"]
    rules = ",".join(f"{r}={n}" for r, n in v["rules"].items()) or "none"
    reproduced = [c for c, r in entry["reproduced"]["cases"].items() if r == REPRODUCED]
    isolated = [r for r, o in entry["reproduced"]["rules"].items() if o == NOT_ISOLATED]
    cut = [r for r, o in entry["reproduced"]["rules"].items() if o == CUT_OFF]
    return (
        f"{entry['attempt_id']} {Path(entry['scenario']).stem}: {v['result']} ({rules}) | "
        f"reproduced {','.join(reproduced) or 'none'}"
        f"{' | ' + NOT_ISOLATED + ': ' + ','.join(isolated) if isolated else ''}"
        f"{' | ' + CUT_OFF + ': ' + ','.join(cut) if cut else ''} | "
        f"located {entry['located']['result']} | runs {entry['oversold_runs']}"
        f"{' | stop: ' + entry['stop_reason'] if entry['stop_reason'] else ''}"
        f"{' | manual check' if entry.get('manual_check') else ''}"
    )


def ledger_path_for(root: Path) -> Path:
    return Path(root) / "runs" / "ledger.jsonl"


def _start(root: Path, version: str, max_runs, raise_dollar_cap):
    totals = ledger.spent(ledger.load(ledger_path_for(root)))
    budget = from_flags(max_runs, raise_dollar_cap, totals["dollars"])
    print(
        f"sweep: ledger so far: {totals['oversold_runs']} Oversold runs, "
        f"{totals['dollars']:.2f} of {budget.total_dollar_cap:.2f} dollars"
        + (
            f", {totals['unsettled_calls']} paid calls never settled, counted at their reservation"
            if totals["unsettled_calls"]
            else ""
        )
    )
    runner = OversoldRunner(root)
    image_id, digest = runner.image(version)
    print(f"sweep: medusa {version} image {image_id} digest {digest}")
    cases = load_cases(Path(root) / "benchmark" / "cases")
    return budget, runner, image_id, digest, cases


def only_inconclusive(attempt: Attempt) -> bool:
    if attempt.entry["setup_error"]:
        return False
    runs = sum(len(h) for h in attempt.histories.values())
    return runs > 0 and sum(attempt.entry["inconclusive"][n] for n in attempt.histories) == runs


def run_attempts(factories, budget: Budget, report=print) -> tuple[list[Attempt], str | None]:
    attempts: list[Attempt] = []
    pending: list[Attempt] = []
    stop = None
    streak = 0
    for factory in factories:
        if budget.session_left() < SCREEN_RUNS:
            stop = (
                f"session runs cap: {budget.session_left()} runs left, a screen needs {SCREEN_RUNS}"
            )
            break
        attempt = factory()
        attempts.append(attempt)
        attempt.first_pass()
        if attempt.done:
            report(describe_entry(attempt.finish()))
        else:
            pending.append(attempt)
        if attempt.stop:
            stop = attempt.stop
            break
        streak = streak + 1 if only_inconclusive(attempt) else 0
        if streak >= HARNESS_STREAK:
            stop = f"harness: {streak} attempts in a row had only inconclusive runs"
            break
    for attempt in pending:
        if stop or budget.session_left() < RETRY_RUNS:
            break
        attempt.second_pass()
        report(describe_entry(attempt.finish()))
        if attempt.stop:
            stop = attempt.stop
    for attempt in pending:
        if not attempt.finished:
            report(describe_entry(attempt.finish()))
    return attempts, stop


def candidate_list_sha256(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        text = Path(path).read_text(encoding="utf-8")
        h.update(f"{Path(path).stem}\n{text}\n".encode())
    return h.hexdigest()


def capped(entry: dict) -> bool:
    return " cap reached: " in (entry.get("stop_reason") or "")


def cut_off(entry: dict, rule: str, case_rules: dict[str, str]) -> bool:
    if not capped(entry):
        return False
    mine = {case_id for case_id, r in case_rules.items() if r == rule}
    ran = {case_id for c in entry["controls"] for case_id in c["cases"]}
    return not mine <= ran


def rule_outcome(entry: dict, rule: str, case_rules: dict[str, str]) -> str:
    outcome = entry["reproduced"]["rules"][rule]
    if outcome == NOT_ISOLATED and cut_off(entry, rule, case_rules):
        return CUT_OFF
    return outcome


def trial_summary(records: list[dict], case_rules: dict[str, str]) -> dict:
    trials = [r for r in records if r.get("kind") == "trial"]
    if len(trials) != 1:
        raise ValueError(f"expected one trial line, found {len(trials)}")
    trial = trials[0]
    entries = [e for e in ledger.attempts(records) if not e.get("interrupted")]
    reached = len({r["attempt_id"] for r in records if r.get("kind") == "started"})
    first: dict[str, int] = {}
    for e in entries:
        for case_id, runs in e["reproduced_at"].items():
            first[case_id] = min(first.get(case_id, runs), runs)
    results = [e["violation"]["result"] for e in entries]
    return {
        "mode": trial["mode"],
        "seed": trial["seed"],
        "order_seed": trial["order_seed"],
        "candidates_sha256": trial["candidates_sha256"],
        "run_cap": trial["run_cap"],
        "runs_used": ledger.spent(records)["oversold_runs"],
        "candidates": trial["candidates"],
        "reached": reached,
        "never_reached": trial["candidates"] - reached,
        "cases": {
            case_id: {"reproduced": case_id in first, "runs_to_first": first.get(case_id)}
            for case_id in sorted(case_rules)
        },
        "cases_reproduced": len(first),
        "violations": results.count(VIOLATION),
        "cause_not_isolated": sum(
            rule_outcome(e, rule, case_rules) == NOT_ISOLATED
            for e in entries
            for rule in e["reproduced"]["rules"]
        ),
        "cut_off_by_run_cap": sum(
            any(rule_outcome(e, rule, case_rules) == CUT_OFF for rule in e["reproduced"]["rules"])
            for e in entries
        ),
        "not_reproduced": sum(r.startswith("not reproduced within") for r in results),
        "unpreparable": results.count(UNPREPARABLE),
        "inconclusive": results.count(INCONCLUSIVE),
        "interrupted": len(ledger.attempts(records)) - len(entries),
        "located": "not applicable",
    }


def run_sweep(
    root: Path,
    paths: list[Path],
    version: str,
    seed: int,
    stamp: str,
    max_runs=None,
    raise_dollar_cap=None,
    mode: str = "grid",
    order_seed: int | None = None,
) -> int:
    try:
        budget, runner, image_id, digest, cases = _start(root, version, max_runs, raise_dollar_cap)
    except RuntimeError as err:
        print(f"sweep: {err}")
        return 2
    ledger_path = ledger_path_for(root)
    refused = []
    factories = []
    for index, path in enumerate(paths, start=1):
        try:
            check_candidate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
        except CandidateRefused as err:
            refused.append(f"{Path(path).stem}: {err}")
            continue
        meta = {
            "attempt_id": f"{stamp}-{index:03d}",
            "source": "sweep",
            "seed": seed,
            "rerun_of": None,
        }

        def factory(path=path, meta=meta):
            return Attempt(
                root,
                path,
                version,
                runner,
                budget,
                cases,
                image_id,
                digest,
                runner.pin,
                meta,
                ledger_path,
            )

        factories.append(factory)
    for note in refused:
        print(f"sweep: refused: {note}")
    trial = {
        "kind": "trial",
        "attempt_id": f"{stamp}-trial",
        "source": "sweep",
        "mode": mode,
        "seed": seed,
        "order_seed": order_seed,
        "medusa_version": version,
        "run_cap": budget.session_runs,
        "candidates": len(paths),
        "candidate_names": [Path(p).stem for p in paths],
        "candidates_sha256": candidate_list_sha256(paths),
        "oversold_commit": runner.pin,
        "timestamp": now(),
    }
    ledger.append(ledger_path, trial)
    print(
        f"sweep: trial {mode} seed {seed} order seed {order_seed}: {len(paths)} candidates, "
        f"list sha256 {trial['candidates_sha256']}, run cap {budget.session_runs}"
    )
    attempts, stop = run_attempts(factories, budget)
    screened = sum(1 for a in attempts if a.entry["screen_runs"])
    retried = sum(1 for a in attempts if a.entry["retry_runs"])
    scored = sum(1 for a in attempts if a.entry["score_runs"])
    print(
        f"sweep: {len(paths)} candidates, {len(refused)} refused, {len(attempts)} attempted, "
        f"{screened} screened, {retried} retried, {scored} scored, "
        f"{len(factories) - len(attempts)} skipped"
    )
    if stop:
        print(f"sweep: stopped: {stop}")
    for a in attempts:
        for note in a.entry["manual_check"]:
            print(f"sweep: manual check: {a.entry['attempt_id']} {Path(a.scenario).stem}: {note}")
    session = [r for r in ledger.load(ledger_path) if r["attempt_id"].startswith(f"{stamp}-")]
    print(json.dumps(ledger.summary(session), indent=2))
    print("sweep: trial summary")
    print(json.dumps(trial_summary(session, {c.id: c.rule for c in cases.values()}), indent=2))
    print(budget.describe())
    if stop and stop.startswith("uncovered"):
        return 3
    return 0


def outcome(entry: dict) -> tuple:
    return (
        entry["violation"]["result"],
        tuple(sorted(entry["violation"]["rules"])),
        tuple(sorted(entry["reproduced"]["cases"].items())),
    )


def rerun(root: Path, attempt_id: str, stamp: str, max_runs=None, raise_dollar_cap=None) -> int:
    ledger_path = ledger_path_for(root)
    old = ledger.find(ledger.load(ledger_path), attempt_id)
    if "violation" not in old:
        print(f"rerun: {attempt_id} is a line from before the three results, not comparable")
        return 2
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

    def factory():
        return Attempt(
            root,
            path,
            old["medusa_version"],
            runner,
            budget,
            cases,
            image_id,
            digest,
            runner.pin,
            meta,
            ledger_path,
        )

    attempts, stop = run_attempts([factory], budget)
    if not attempts:
        print(f"rerun: stopped before the attempt started: {stop}")
        return 2
    entry = attempts[0].entry
    for note in entry["manual_check"]:
        print(f"rerun: manual check: {note}")
    same = outcome(entry) == outcome(old)
    print(f"rerun: before {outcome(old)}, now {outcome(entry)}")
    print(f"rerun: same results: {'yes' if same else 'no'}")
    print(budget.describe())
    if stop:
        print(f"rerun: stopped: {stop}")
    return 0 if same else 1
