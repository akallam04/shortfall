import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from shortfall.cases import strict_load

SCHEMA = "shortfall.answer/v2"
CAUSES_SCHEMA = "shortfall.causes/v1"
FILE = "answer.yaml"
CAUSES_FILE = "causes.yaml"
ACCEPTED = "accepted"
NOT_ACCEPTED = "not accepted"
NOT_NAMED = "not named"
NOT_APPLICABLE = "not applicable"
PARTS = ("file", "cause", "located")
_PATH = re.compile(r"packages(/[A-Za-z0-9_.@-]+)+")
_ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


@dataclass(frozen=True)
class Answer:
    files: tuple[str, ...]
    causes: tuple[str, ...]


def causes_path(folder: str | Path) -> Path:
    return Path(folder).resolve().parent.parent / CAUSES_FILE


def load_causes(path: str | Path) -> dict[str, str]:
    path = Path(path)
    data = strict_load(path.read_text(encoding="utf-8"))
    problems = []
    if not isinstance(data, dict):
        raise ValueError(f"{path}: must be a mapping")
    for key in data:
        if key not in ("schema", "causes"):
            problems.append(f"unknown field {key}")
    if data.get("schema") != CAUSES_SCHEMA:
        problems.append(f"schema must be {CAUSES_SCHEMA}")
    items = data.get("causes")
    if not isinstance(items, list) or not items:
        problems.append("causes must be a list of one or more causes")
        items = []
    out: dict[str, str] = {}
    for i, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != {"id", "description"}:
            problems.append(f"causes[{i}] must have exactly an id and a description")
            continue
        cause_id, description = item["id"], item["description"]
        if not isinstance(cause_id, str) or not _ID.fullmatch(cause_id):
            problems.append(f"causes[{i}].id must be kebab-case")
        elif cause_id in out:
            problems.append(f"causes[{i}].id {cause_id} repeats")
        elif not isinstance(description, str) or not description.strip():
            problems.append(f"causes[{i}].description must be text")
        else:
            out[cause_id] = description
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return out


def load_answer(folder: str | Path, causes: dict[str, str] | None = None) -> Answer:
    folder = Path(folder)
    if causes is None:
        causes = load_causes(causes_path(folder))
    path = folder / FILE
    data = strict_load(path.read_text(encoding="utf-8"))
    problems = []
    if not isinstance(data, dict):
        raise ValueError(f"{path}: must be a mapping")
    for key in data:
        if key not in ("schema", "case", "files", "causes"):
            problems.append(f"unknown field {key}")
    if data.get("schema") != SCHEMA:
        problems.append(f"schema must be {SCHEMA}")
    if data.get("case") != folder.name:
        problems.append(f"case must be {folder.name}")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        problems.append("files must be a list of one or more paths")
        files = []
    for i, f in enumerate(files):
        if not isinstance(f, str) or not _PATH.fullmatch(f) or "/../" in f + "/" or "/./" in f:
            problems.append(f"files[{i}] must be a path under packages/ in the Medusa source")
    if len(set(map(str, files))) != len(files):
        problems.append("files must not repeat")
    named = data.get("causes")
    if not isinstance(named, list) or not named:
        problems.append("causes must be a list of one or more causes")
        named = []
    for i, c in enumerate(named):
        if c not in causes:
            problems.append(f"causes[{i}] must be one of the benchmark's causes")
    if len(set(map(str, named))) != len(named):
        problems.append("causes must not repeat")
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return Answer(files=tuple(files), causes=tuple(named))


def grade(folder: str | Path, file: str | None, cause: str | None) -> dict[str, str]:
    answer = load_answer(folder)
    out = {
        "file": NOT_NAMED if file is None else (ACCEPTED if file in answer.files else NOT_ACCEPTED),
        "cause": NOT_NAMED
        if cause is None
        else (ACCEPTED if cause in answer.causes else NOT_ACCEPTED),
    }
    both = out["file"] == ACCEPTED and out["cause"] == ACCEPTED
    out["located"] = ACCEPTED if both else NOT_ACCEPTED
    return out


def located(
    cases: dict[str, Path], reproduced: list[str], file: str | None, cause: str | None = None
) -> dict:
    if file is None and cause is None:
        return {"result": NOT_APPLICABLE}
    return {
        "result": "graded",
        "file": file,
        "cause": cause,
        "cases": {case_id: grade(cases[case_id], file, cause) for case_id in reproduced},
    }


def fixed_guess(folders: list[Path], file: str | None = None, cause: str | None = None) -> dict:
    out = {"cases": len(folders), **dict.fromkeys(PARTS, 0)}
    for folder in folders:
        graded = grade(folder, file, cause)
        for part in PARTS:
            out[part] += graded[part] == ACCEPTED
    return out


def most_common(folders: list[Path], field: str) -> tuple[str, int]:
    seen: Counter = Counter()
    order: list[str] = []
    for folder in folders:
        for value in getattr(load_answer(folder), field):
            seen[value] += 1
            if value not in order:
                order.append(value)
    best = max(seen.values())
    return next(v for v in order if seen[v] == best), best
