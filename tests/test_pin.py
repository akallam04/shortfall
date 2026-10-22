from pathlib import Path

import pytest

from shortfall.pin import OVERSOLD_REPO, read_pin

LOCK = Path(__file__).resolve().parent.parent / "oversold.lock"
GOOD_COMMIT = "a18d5c9f3892dbca86effa0766e975985f8324bd"


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "oversold.lock"
    path.write_text(text, encoding="utf-8")
    return path


def test_real_lock_parses():
    repo, commit = read_pin(LOCK)
    assert repo == OVERSOLD_REPO
    assert len(commit) == 40


def test_good_lock(tmp_path):
    path = write(tmp_path, f"repo={OVERSOLD_REPO}\ncommit={GOOD_COMMIT}\n")
    assert read_pin(path) == (OVERSOLD_REPO, GOOD_COMMIT)


@pytest.mark.parametrize(
    "text",
    [
        f"commit={GOOD_COMMIT}\n",
        f"repo={OVERSOLD_REPO}\n",
        "",
        f"repo=https://github.com/someone/oversold.git\ncommit={GOOD_COMMIT}\n",
        f"repo=https://github.com/akallam04/oversold\ncommit={GOOD_COMMIT}\n",
        f"repo={OVERSOLD_REPO}\ncommit={GOOD_COMMIT.upper()}\n",
        f"repo={OVERSOLD_REPO}\ncommit={GOOD_COMMIT[:39]}\n",
        f"repo={OVERSOLD_REPO}\ncommit={GOOD_COMMIT}0\n",
        f"repo={OVERSOLD_REPO}\ncommit={GOOD_COMMIT[:39]}g\n",
        f"repo={OVERSOLD_REPO}\ncommit=main\n",
    ],
    ids=[
        "missing-repo",
        "missing-commit",
        "empty",
        "other-repo",
        "repo-without-git-suffix",
        "uppercase-commit",
        "short-commit",
        "long-commit",
        "non-hex-commit",
        "branch-name",
    ],
)
def test_bad_lock_raises(tmp_path, text):
    with pytest.raises(ValueError):
        read_pin(write(tmp_path, text))
