import re
from pathlib import Path

OVERSOLD_REPO = "https://github.com/akallam04/oversold.git"
_COMMIT = re.compile(r"[0-9a-f]{40}")


def read_pin(path: str | Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()

    for key in ("repo", "commit"):
        if key not in values:
            raise ValueError(f"oversold.lock is missing {key}=")

    repo = values["repo"]
    commit = values["commit"]
    if repo != OVERSOLD_REPO:
        raise ValueError(f"oversold.lock repo must be {OVERSOLD_REPO}, got {repo!r}")
    if not _COMMIT.fullmatch(commit):
        raise ValueError(f"oversold.lock commit must be 40 lowercase hex, got {commit!r}")
    return repo, commit
