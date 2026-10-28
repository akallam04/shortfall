import os
import shutil
from pathlib import Path

import pytest

from shortfall.tools import (
    MAX_CHARS,
    MAX_LINES,
    MAX_MATCH_LINE,
    MAX_MATCHES,
    Snapshot,
    ToolError,
    cut,
)

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent / "data" / "snapshot"
SECRETS = {
    ".env": "SECRET-ENV",
    ".oversold/compose.yaml": "SECRET-OVERSOLD",
    "benchmark/cases/medusa-x/reference.yaml": "SECRET-BENCHMARK",
    "tests/test_x.py": "SECRET-TESTS",
    "runs/ledger.jsonl": "SECRET-RUNS",
    "snapshots/issues/medusa-x.md": "SECRET-ISSUE",
}


@pytest.fixture
def snap():
    return Snapshot(FIXTURE)


@pytest.fixture
def repo(tmp_path):
    for rel, text in SECRETS.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")
    root = tmp_path / "snapshots" / "medusa-test"
    shutil.copytree(FIXTURE, root)
    return tmp_path, root


def test_list_files(snap):
    assert snap.list_files() == ".: 1 folders, 0 files\npackages/"
    out = snap.list_files("packages")
    assert out.splitlines() == [
        "packages: 2 folders, 1 files",
        "README.md (49 bytes)",
        "core/",
        "modules/",
    ]
    assert snap.list_files("./packages/") == out


def test_list_files_empty_folder_and_file(repo):
    _, root = repo
    (root / "packages" / "empty").mkdir()
    snap = Snapshot(root)
    assert snap.list_files("packages/empty") == "packages/empty: 0 folders, 0 files\n(empty)"
    with pytest.raises(ToolError, match="not a folder"):
        snap.list_files("packages/README.md")


def test_read_file(snap):
    out = snap.read_file("packages/core/src/cart.ts")
    assert out.splitlines() == [
        "packages/core/src/cart.ts, lines 1 to 5 of 5",
        "     1\texport function reserveInventory(items) {",
        "     2\t  return items.map((item) => item.quantity)",
        "     3\t}",
        "     4\t",
        '     5\texport const LOCK_KEY = "cart"',
    ]
    assert snap.read_file("packages/core/src/cart.ts", 2, 3).splitlines()[1:] == [
        "     2\t  return items.map((item) => item.quantity)",
        "     3\t}",
    ]


@pytest.mark.parametrize(
    "start,end,message",
    [(0, None, "start"), (2, 1, "end"), (True, None, "start"), (1, 2.5, "end"), (9, None, "past")],
)
def test_read_file_bad_ranges(snap, start, end, message):
    with pytest.raises(ToolError, match=message):
        snap.read_file("packages/core/src/cart.ts", start, end)


def test_read_file_refuses_folders_binary_and_missing(repo):
    _, root = repo
    (root / "packages" / "logo.png").write_bytes(b"\x89PNG\0\0data")
    (root / "packages" / "blank.ts").write_text("")
    snap = Snapshot(root)
    with pytest.raises(ToolError, match="not a file"):
        snap.read_file("packages")
    with pytest.raises(ToolError, match="binary"):
        snap.read_file("packages/logo.png")
    with pytest.raises(ToolError, match="not found"):
        snap.read_file("packages/nope.ts")
    assert snap.read_file("packages/blank.ts") == "packages/blank.ts: empty file"


def test_read_file_stops_at_400_lines(repo):
    _, root = repo
    (root / "packages" / "long.ts").write_text("".join(f"line {n}\n" for n in range(1, 1001)))
    snap = Snapshot(root)
    first = snap.read_file("packages/long.ts").splitlines()
    assert first[0] == "packages/long.ts, lines 1 to 400 of 1000"
    assert len(first) == MAX_LINES + 2
    assert first[-2] == "   400\tline 400"
    assert first[-1] == "[600 more lines, read on with start=401]"
    asked = snap.read_file("packages/long.ts", 101, 1000).splitlines()
    assert asked[0] == "packages/long.ts, lines 101 to 500 of 1000"
    assert asked[-1] == "[at most 400 lines per call, read on with start=501]"
    tail = snap.read_file("packages/long.ts", 990, 2000).splitlines()
    assert tail[0] == "packages/long.ts, lines 990 to 1000 of 1000"
    assert tail[-1] == "  1000\tline 1000"


def test_read_file_is_cut_at_40000_characters(repo):
    _, root = repo
    (root / "packages" / "wide.ts").write_text(("y" * 300 + "\n") * 400)
    out = Snapshot(root).read_file("packages/wide.ts")
    full = len("packages/wide.ts, lines 1 to 400 of 400") + 400 * (1 + 7 + 300)
    assert len(out) == MAX_CHARS
    assert out.endswith(f"[cut at {MAX_CHARS} characters, the full result was {full} characters]")


def test_search(snap):
    out = snap.search("reserveInventory")
    assert out.splitlines() == [
        "2 matches for 'reserveInventory' under .",
        "packages/core/src/cart.ts:1: export function reserveInventory(items) {",
        "packages/modules/inventory/src/service.ts:3: return reserveInventory([{ quantity }])",
    ]
    one = snap.search("reserveInventory", "packages/modules")
    assert one.splitlines()[0] == "1 matches for 'reserveInventory' under packages/modules"
    assert snap.search("LOCK_KEY", "packages/core/src/cart.ts").splitlines()[1] == (
        'packages/core/src/cart.ts:5: export const LOCK_KEY = "cart"'
    )
    assert snap.search("reserveinventory") == "no matches for 'reserveinventory' under ."
    assert snap.search("(item) =>").splitlines()[0].startswith("1 matches")


@pytest.mark.parametrize("text", ["", "a\nb", None])
def test_search_bad_text(snap, text):
    with pytest.raises(ToolError, match="text"):
        snap.search(text)


def test_search_stops_at_50_matches_and_cuts_long_lines(repo):
    _, root = repo
    (root / "packages" / "many.ts").write_text("hit\n" * 60)
    (root / "packages" / "wide.ts").write_text("hit " + "z" * 1000 + "\n")
    (root / "packages" / "logo.png").write_bytes(b"\0hit")
    snap = Snapshot(root)
    out = snap.search("hit", "packages").splitlines()
    assert out[0] == "first 50 matches for 'hit' under packages"
    assert len(out) == MAX_MATCHES + 2
    assert out[-1] == "[stopped at 50 matches, narrow the path or the text]"
    assert not any("logo.png" in line for line in out)
    wide = snap.search("hit", "packages/wide.ts").splitlines()[1]
    assert wide == "packages/wide.ts:1: hit " + "z" * (MAX_MATCH_LINE - 4) + "..."


def test_list_files_is_cut_at_40000_characters(repo):
    _, root = repo
    many = root / "packages" / "many"
    many.mkdir()
    for n in range(1000):
        (many / f"{n:04d}-{'n' * 60}.ts").write_text("")
    out = Snapshot(root).list_files("packages/many")
    assert len(out) == MAX_CHARS
    assert "[cut at 40000 characters" in out


def test_cut():
    assert cut("short") == "short"
    text = "a" * (MAX_CHARS + 5)
    out = cut(text)
    assert len(out) == MAX_CHARS
    assert out.endswith(f"the full result was {MAX_CHARS + 5} characters]")


ESCAPES = [
    "..",
    "../",
    "../issues/medusa-x.md",
    "../../.env",
    "../../.oversold/compose.yaml",
    "../../benchmark/cases/medusa-x/reference.yaml",
    "../../tests/test_x.py",
    "../../runs/ledger.jsonl",
    "packages/../../issues/medusa-x.md",
    "packages/..",
    "packages\\..\\..\\..\\.env",
    "~/.env",
    "C:\\Windows",
]


@pytest.mark.parametrize("path", ESCAPES)
def test_relative_escapes_are_refused(repo, path):
    _, root = repo
    snap = Snapshot(root)
    for call in (snap.list_files, snap.read_file, lambda p: snap.search("SECRET", p)):
        with pytest.raises(ToolError, match="not allowed"):
            call(path)


@pytest.mark.parametrize("rel", sorted(SECRETS))
def test_absolute_paths_outside_are_refused(repo, rel):
    base, root = repo
    snap = Snapshot(root)
    for path in (str(base / rel), str(base / rel).replace("/", "//"), str(root / "packages")):
        with pytest.raises(ToolError, match="absolute"):
            snap.read_file(path)


@pytest.mark.parametrize("rel", sorted(SECRETS))
def test_links_pointing_outside_are_refused(repo, rel):
    base, root = repo
    secret = SECRETS[rel]
    os.symlink(base / rel, root / "packages" / "abs-link")
    os.symlink(os.path.relpath(base / rel, root / "packages"), root / "packages" / "rel-link")
    os.symlink(base / Path(rel).parts[0], root / "packages" / "dir-link")
    snap = Snapshot(root)
    for path in ("packages/abs-link", "packages/rel-link"):
        with pytest.raises(ToolError, match="outside the snapshot"):
            snap.read_file(path)
        with pytest.raises(ToolError, match="outside the snapshot"):
            snap.search("SECRET", path)
    for call in (snap.list_files, lambda p: snap.search("SECRET", p)):
        with pytest.raises(ToolError, match="outside the snapshot"):
            call("packages/dir-link")
    inner = "/".join(("packages/dir-link", *Path(rel).parts[1:]))
    with pytest.raises(ToolError, match="outside the snapshot"):
        snap.read_file(inner)
    listing = snap.list_files("packages")
    assert "abs-link (link outside the snapshot)" in listing
    assert "dir-link (link outside the snapshot)" in listing
    assert secret not in listing
    assert snap.search("SECRET") == "no matches for 'SECRET' under ."
    assert secret not in snap.search("SECRET", "packages")


def test_links_inside_the_snapshot_work(repo):
    _, root = repo
    os.symlink("core/src/cart.ts", root / "packages" / "cart-link.ts")
    os.symlink("core", root / "packages" / "core-link")
    snap = Snapshot(root)
    assert "LOCK_KEY" in snap.read_file("packages/cart-link.ts")
    assert "cart.ts (" in snap.list_files("packages/core-link/src")
    assert "cart-link.ts (" in snap.list_files("packages")
    assert "packages/cart-link.ts:5:" in snap.search("LOCK_KEY")


def test_a_link_loop_is_refused(repo):
    _, root = repo
    os.symlink("loop-b", root / "packages" / "loop-a")
    os.symlink("loop-a", root / "packages" / "loop-b")
    snap = Snapshot(root)
    with pytest.raises(ToolError):
        snap.read_file("packages/loop-a")
    assert "loop-a (broken link)" in snap.list_files("packages")
    assert snap.search("SECRET") == "no matches for 'SECRET' under ."


def test_the_real_repo_is_out_of_reach_from_the_fixture(snap):
    for rel in ("benchmark/README.md", "tests/test_tools.py", "oversold.lock", ".gitignore"):
        with pytest.raises(ToolError, match="not allowed"):
            snap.read_file("../../../" + rel)
        with pytest.raises(ToolError, match="absolute"):
            snap.read_file(str(ROOT / rel))
    with pytest.raises(ToolError, match="not allowed"):
        snap.list_files("../../..")
    assert "SECRET" not in snap.search("e")


def test_non_text_paths_are_refused(snap):
    for path in (None, 3, Path("packages")):
        with pytest.raises(ToolError, match="text"):
            snap.read_file(path)
    with pytest.raises(ToolError, match="NUL"):
        snap.read_file("packages/\0README.md")
