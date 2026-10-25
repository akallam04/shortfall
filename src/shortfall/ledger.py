import json
import os
from collections import Counter
from pathlib import Path

VERDICTS = ("match", "no match", "reproduction only", "inconclusive", "unpreparable")
INTERRUPTED = "interrupted"
SOURCES = ("sweep",)
KINDS = ("started", "spend", "final")
SPEND_ITEMS = ("oversold_runs", "paid_call")

FINAL_FIELDS = (
    "kind",
    "attempt_id",
    "source",
    "seed",
    "scenario",
    "scenario_sha256",
    "case",
    "cases",
    "medusa_version",
    "carts",
    "servers",
    "shape",
    "screen_runs",
    "score_runs",
    "control_runs",
    "candidate_fails",
    "control_fails",
    "inconclusive",
    "rules_failed",
    "verdict",
    "wall_seconds",
    "oversold_runs",
    "dollars",
    "oversold_commit",
    "medusa_image_id",
    "medusa_image_digest",
    "run_folders",
    "stop_reason",
    "setup_error",
    "manual_check",
    "rerun_of",
    "timestamp",
)
LEGACY_OPTIONAL = ("kind", "dollars", "rerun_of", "stop_reason", "setup_error", "manual_check")
LEGACY_REQUIRED = tuple(f for f in FINAL_FIELDS if f not in LEGACY_OPTIONAL)
FINAL_REQUIRED = (*LEGACY_REQUIRED, "kind", "dollars")

STARTED_FIELDS = (
    "kind",
    "attempt_id",
    "source",
    "seed",
    "scenario",
    "scenario_sha256",
    "medusa_version",
    "medusa_image_id",
    "oversold_commit",
    "rerun_of",
    "timestamp",
)
STARTED_REQUIRED = tuple(f for f in STARTED_FIELDS if f != "rerun_of")

SPEND_FIELDS = (
    "kind",
    "attempt_id",
    "spend_id",
    "item",
    "state",
    "set",
    "oversold_runs",
    "model",
    "input_tokens",
    "output_tokens",
    "dollars",
    "timestamp",
)

FIELDS = {"started": STARTED_FIELDS, "spend": SPEND_FIELDS, "final": FINAL_FIELDS}


def _local_markers() -> list[str]:
    home = os.path.expanduser("~")
    if not home or home in ("~", "/"):
        return []
    return [home, os.path.dirname(home.rstrip("/")) + "/"]


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(value, list | tuple):
        for v in value:
            yield from _strings(v)


def _is_count(value) -> bool:
    return type(value) is int and value >= 0


def _is_dollars(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value >= 0


def _check_spend(entry: dict, problems: list[str]) -> None:
    item = entry.get("item")
    state = entry.get("state")
    if item not in SPEND_ITEMS:
        problems.append(f"item must be one of {', '.join(SPEND_ITEMS)}")
        return
    if not _is_dollars(entry.get("dollars")):
        problems.append("dollars must be 0 or more")
    if item == "oversold_runs":
        if state != "charged":
            problems.append("an oversold_runs spend must be charged")
        if not (_is_count(entry.get("oversold_runs")) and entry["oversold_runs"] > 0):
            problems.append("oversold_runs must be above 0")
        if entry.get("dollars") != 0:
            problems.append("an oversold_runs spend costs 0 dollars")
        if entry.get("model") is not None:
            problems.append("an oversold_runs spend has no model")
        return
    if state not in ("reserved", "settled"):
        problems.append("a paid_call spend must be reserved or settled")
    if not (isinstance(entry.get("model"), str) and entry["model"].strip()):
        problems.append("a paid_call spend needs a model")
    if entry.get("oversold_runs") not in (None, 0):
        problems.append("a paid_call spend has no oversold runs")
    tokens = (entry.get("input_tokens"), entry.get("output_tokens"))
    if state == "settled" and not all(_is_count(t) for t in tokens):
        problems.append("a settled paid_call needs input_tokens and output_tokens")
    if state == "reserved" and any(t is not None for t in tokens):
        problems.append("a reserved paid_call has no tokens yet")


def validate(entry: dict, legacy: bool = True) -> None:
    problems = []
    kind = entry.get("kind")
    if kind is None and not legacy:
        problems.append("kind is required")
    if kind is not None and kind not in KINDS:
        problems.append(f"kind must be one of {', '.join(KINDS)}")
        raise ValueError("ledger entry: " + "; ".join(problems))
    fields = FIELDS[kind or "final"]
    required = {
        None: LEGACY_REQUIRED,
        "final": FINAL_REQUIRED,
        "started": STARTED_REQUIRED,
        "spend": SPEND_FIELDS,
    }[kind]
    for key in entry:
        if key not in fields:
            problems.append(f"unknown field {key}")
    for key in required:
        if key not in entry:
            problems.append(f"{key} is required")
    if kind in (None, "final") and entry.get("verdict") not in VERDICTS:
        problems.append(f"verdict must be one of {', '.join(VERDICTS)}")
    if kind in (None, "final", "started") and entry.get("source") not in SOURCES:
        problems.append(f"source must be one of {', '.join(SOURCES)}")
    if kind == "final" and not _is_dollars(entry.get("dollars")):
        problems.append("dollars must be 0 or more")
    if kind == "spend":
        _check_spend(entry, problems)
    markers = _local_markers()
    for text in _strings(entry):
        if text.startswith("/") or any(m in text for m in markers):
            problems.append(f"value looks like a local path: {text[:40]!r}")
            break
    if problems:
        raise ValueError("ledger entry: " + "; ".join(problems))


def append(path: str | Path, entry: dict) -> None:
    validate(entry, legacy=False)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({k: entry.get(k) for k in FIELDS[entry["kind"]]}, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def load(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as err:
            raise ValueError(f"{path.name} line {number}: not JSON: {err}") from err
        validate(record)
        records.append(record)
    return records


def _is_final(record: dict) -> bool:
    return record.get("kind") in (None, "final")


def _spend_by_attempt(records: list[dict]) -> dict[str, dict]:
    runs: Counter = Counter()
    paid: dict[str, dict[str, dict]] = {}
    for r in records:
        if r.get("kind") != "spend":
            continue
        if r["item"] == "oversold_runs":
            runs[r["attempt_id"]] += r["oversold_runs"]
        else:
            calls = paid.setdefault(r["attempt_id"], {})
            if r["state"] == "settled" or r["spend_id"] not in calls:
                calls[r["spend_id"]] = r
    out: dict[str, dict] = {}
    for attempt_id in set(runs) | set(paid):
        calls = paid.get(attempt_id, {})
        out[attempt_id] = {
            "oversold_runs": runs.get(attempt_id, 0),
            "dollars": sum(c["dollars"] for c in calls.values()),
            "paid_calls": len(calls),
            "unsettled_calls": sum(1 for c in calls.values() if c["state"] == "reserved"),
        }
    return out


def attempts(records: list[dict]) -> list[dict]:
    spends = _spend_by_attempt(records)
    order: list[str] = []
    finals: dict[str, dict] = {}
    started: dict[str, dict] = {}
    for r in records:
        attempt_id = r["attempt_id"]
        if attempt_id not in order:
            order.append(attempt_id)
        if _is_final(r):
            finals[attempt_id] = r
        elif r["kind"] == "started":
            started[attempt_id] = r
    out = []
    for attempt_id in order:
        if attempt_id in finals:
            out.append(finals[attempt_id])
        elif attempt_id in started:
            spent = spends.get(attempt_id, {"oversold_runs": 0, "dollars": 0.0})
            s = started[attempt_id]
            out.append(
                {
                    "attempt_id": attempt_id,
                    "source": s["source"],
                    "scenario": s["scenario"],
                    "medusa_version": s["medusa_version"],
                    "verdict": INTERRUPTED,
                    "case": None,
                    "cases": [],
                    "oversold_runs": spent["oversold_runs"],
                    "dollars": spent["dollars"],
                    "wall_seconds": 0.0,
                    "rerun_of": s.get("rerun_of"),
                    "timestamp": s["timestamp"],
                }
            )
    return out


def spent(records: list[dict]) -> dict:
    spends = _spend_by_attempt(records)
    runs = 0
    dollars = 0.0
    counted = set()
    for attempt_id, s in spends.items():
        runs += s["oversold_runs"]
        dollars += s["dollars"]
        counted.add(attempt_id)
    for r in records:
        if _is_final(r) and r["attempt_id"] not in counted:
            runs += r["oversold_runs"]
            dollars += r.get("dollars") or 0.0
            counted.add(r["attempt_id"])
    unsettled = sum(s["unsettled_calls"] for s in spends.values())
    return {"oversold_runs": runs, "dollars": round(dollars, 6), "unsettled_calls": unsettled}


def find(records: list[dict], attempt_id: str) -> dict:
    for entry in attempts(records):
        if entry["attempt_id"] == attempt_id and entry["verdict"] != INTERRUPTED:
            return entry
    raise KeyError(f"no finished attempt {attempt_id} in the ledger")


def summary(records: list[dict]) -> dict:
    entries = attempts(records)
    by_verdict = Counter(e["verdict"] for e in entries)
    by_case: dict[str, Counter] = {}
    for e in entries:
        key = e["case"] if e["case"] is not None else "none"
        by_case.setdefault(key, Counter())[e["verdict"]] += 1
    totals = spent(records)
    return {
        "attempts": len(entries),
        "by_verdict": {v: by_verdict.get(v, 0) for v in (*VERDICTS, INTERRUPTED)},
        "by_case": {k: dict(sorted(v.items())) for k, v in sorted(by_case.items())},
        "oversold_runs": totals["oversold_runs"],
        "dollars": totals["dollars"],
        "wall_seconds": round(sum(e["wall_seconds"] for e in entries), 1),
    }
