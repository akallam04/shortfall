import json
import os
from collections import Counter
from pathlib import Path

VERDICTS = ("match", "no match", "reproduction only", "inconclusive")
SOURCES = ("sweep",)

FIELDS = (
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
    "oversold_commit",
    "medusa_image_id",
    "medusa_image_digest",
    "run_folders",
    "stop_reason",
    "rerun_of",
    "timestamp",
)

REQUIRED = tuple(f for f in FIELDS if f not in ("rerun_of", "stop_reason"))


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


def validate(entry: dict) -> None:
    problems = []
    for key in entry:
        if key not in FIELDS:
            problems.append(f"unknown field {key}")
    for key in REQUIRED:
        if key not in entry:
            problems.append(f"{key} is required")
    if entry.get("verdict") not in VERDICTS:
        problems.append(f"verdict must be one of {', '.join(VERDICTS)}")
    if entry.get("source") not in SOURCES:
        problems.append(f"source must be one of {', '.join(SOURCES)}")
    markers = _local_markers()
    for text in _strings(entry):
        if text.startswith("/") or any(m in text for m in markers):
            problems.append(f"value looks like a local path: {text[:40]!r}")
            break
    if problems:
        raise ValueError("ledger entry: " + "; ".join(problems))


def append(path: str | Path, entry: dict) -> None:
    validate(entry)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({k: entry.get(k) for k in FIELDS}, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as err:
            raise ValueError(f"{path.name} line {number}: not JSON: {err}") from err
        validate(entry)
        entries.append(entry)
    return entries


def find(entries: list[dict], attempt_id: str) -> dict:
    for entry in entries:
        if entry["attempt_id"] == attempt_id:
            return entry
    raise KeyError(f"no attempt {attempt_id} in the ledger")


def summary(entries: list[dict]) -> dict:
    by_verdict = Counter(e["verdict"] for e in entries)
    by_case: dict[str, Counter] = {}
    for e in entries:
        key = e["case"] if e["case"] is not None else "none"
        by_case.setdefault(key, Counter())[e["verdict"]] += 1
    return {
        "attempts": len(entries),
        "by_verdict": {v: by_verdict.get(v, 0) for v in VERDICTS},
        "by_case": {k: dict(sorted(v.items())) for k, v in sorted(by_case.items())},
        "oversold_runs": sum(e["oversold_runs"] for e in entries),
        "wall_seconds": round(sum(e["wall_seconds"] for e in entries), 1),
    }
