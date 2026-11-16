import re
from pathlib import Path

from shortfall.cases import strict_load

SCHEMA = "shortfall.answer/v1"
FILE = "answer.yaml"
ACCEPTED = "accepted"
NOT_ACCEPTED = "not accepted"
NOT_APPLICABLE = "not applicable"
_PATH = re.compile(r"packages(/[A-Za-z0-9_.@-]+)+")


def load_answer(folder: str | Path) -> tuple[str, ...]:
    folder = Path(folder)
    path = folder / FILE
    data = strict_load(path.read_text(encoding="utf-8"))
    problems = []
    if not isinstance(data, dict):
        raise ValueError(f"{path}: must be a mapping")
    for key in data:
        if key not in ("schema", "case", "files"):
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
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return tuple(files)


def grade(folder: str | Path, named: str) -> str:
    return ACCEPTED if named in load_answer(folder) else NOT_ACCEPTED


def located(cases: dict[str, Path], reproduced: list[str], named: str | None) -> dict:
    if named is None:
        return {"result": NOT_APPLICABLE}
    return {
        "result": "graded",
        "file": named,
        "cases": {case_id: grade(cases[case_id], named) for case_id in reproduced},
    }
