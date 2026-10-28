import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from shortfall import snapshot
from shortfall.cases import load_case

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "benchmark" / "cases"
SNAPSHOTS = ROOT / "benchmark" / "snapshots"
FIELDS = [
    "schema",
    "engine",
    "version",
    "repo",
    "tag",
    "commit",
    "folders",
    "removed",
    "files",
    "links",
    "bytes",
    "sha256",
    "ts_files",
]


def write(base: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def git(cwd: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    return subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


SOURCE = {
    "README.md": "top level, not copied\n",
    ".changeset/brave-cats.md": "top level changeset\n",
    "packages/core/CHANGELOG.md": "# changes\n",
    "packages/core/src/cart.ts": "export const a = 1\n",
    "packages/core/src/big.ts": "x" * 500 + "\n",
    "packages/modules/inventory/changelog.md": "# lower case\n",
    "packages/modules/inventory/.changeset/x.md": "nested changeset\n",
    "packages/modules/inventory/src/service.ts": "export class S {}\n",
    "packages/modules/inventory/README.md": "inventory\n",
}


@pytest.fixture
def upstream(tmp_path, monkeypatch):
    repo = tmp_path / "upstream"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    write(repo, SOURCE)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "release")
    git(repo, "tag", "v1.2.3")
    write(repo, {"packages/core/src/cart.ts": "export const a = 2\n"})
    git(repo, "commit", "-q", "-am", "after the release")
    monkeypatch.setattr(snapshot, "MEDUSA_REPO", repo.as_uri())
    root = tmp_path / "shortfall"
    root.mkdir()
    return repo, root


def test_source_snapshot_keeps_only_packages_without_history(upstream):
    repo, root = upstream
    record, same = snapshot.build_source("1.2.3", root)
    assert same is None
    out = root / "snapshots" / "medusa-1.2.3"
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    assert files == [
        "packages/core/src/big.ts",
        "packages/core/src/cart.ts",
        "packages/modules/inventory/README.md",
        "packages/modules/inventory/src/service.ts",
    ]
    assert (out / "packages/core/src/cart.ts").read_text() == "export const a = 1\n"
    assert not list(out.rglob(".git")) and not list(out.rglob(".changeset"))
    assert not (root / "snapshots" / ".build-medusa-1.2.3").exists()
    tag_commit = git(repo, "rev-parse", "v1.2.3").strip()
    assert record["tag"] == "v1.2.3"
    assert record["commit"] == tag_commit
    assert record["removed"] == {"CHANGELOG.md": 2, ".changeset": 1}
    assert record["files"] == 4
    assert record["bytes"] == sum((out / f).stat().st_size for f in files)
    assert record["ts_files"] == {"count": 3, "median_chars": 19, "p90_chars": 501}
    assert list(record) == FIELDS
    saved = json.loads((root / "benchmark/snapshots/medusa-1.2.3.json").read_text())
    assert saved == record


def test_building_twice_gives_the_same_manifest(upstream):
    _, root = upstream
    first, _ = snapshot.build_source("1.2.3", root)
    text = (root / "benchmark/snapshots/medusa-1.2.3.json").read_text()
    second, same = snapshot.build_source("1.2.3", root)
    assert same is True
    assert first == second
    assert (root / "benchmark/snapshots/medusa-1.2.3.json").read_text() == text


def test_manifest_has_no_local_paths(upstream):
    _, root = upstream
    snapshot.build_source("1.2.3", root)
    text = (root / "benchmark/snapshots/medusa-1.2.3.json").read_text()
    assert str(root) not in text
    assert "snapshots/" not in text


def test_missing_tag_leaves_nothing_behind(upstream):
    _, root = upstream
    with pytest.raises(RuntimeError, match="git clone failed"):
        snapshot.build_source("9.9.9", root)
    assert list((root / "snapshots").iterdir()) == []
    assert not (root / "benchmark").exists()


@pytest.mark.parametrize("version", ["v1.2.3", "1.2", "latest", "01.2.3"])
def test_bad_versions_are_refused(tmp_path, version):
    with pytest.raises(ValueError, match="version"):
        snapshot.build_source(version, tmp_path)


def test_manifest_hash_is_over_sorted_paths_and_file_hashes(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    write(a, {"packages/z.ts": "z\n", "packages/a/b.ts": "ab\n"})
    write(b, {"packages/a/b.ts": "ab\n", "packages/z.ts": "z\n"})
    ma = snapshot.manifest(a)
    assert ma == snapshot.manifest(b)
    lines = "".join(
        f"{hashlib.sha256(text.encode()).hexdigest()}  {rel}\n"
        for rel, text in [("packages/a/b.ts", "ab\n"), ("packages/z.ts", "z\n")]
    )
    assert ma["sha256"] == hashlib.sha256(lines.encode()).hexdigest()
    write(b, {"packages/z.ts": "Z\n"})
    assert snapshot.manifest(b)["sha256"] != ma["sha256"]
    (b / "packages/z.ts").rename(b / "packages/y.ts")
    assert snapshot.manifest(b)["sha256"] != ma["sha256"]


def test_links_are_hashed_by_target(tmp_path):
    write(tmp_path, {"packages/a.ts": "a\n"})
    os.symlink("a.ts", tmp_path / "packages" / "b.ts")
    m = snapshot.manifest(tmp_path)
    assert (m["files"], m["links"], m["bytes"], m["ts_files"]["count"]) == (2, 1, 2, 1)


def test_clean_counts_what_it_removes(tmp_path):
    write(
        tmp_path,
        {
            "packages/a/CHANGELOG.md": "",
            "packages/b/Changelog.md": "",
            "packages/b/.changeset/one.md": "",
            "packages/b/src/changelog.ts": "",
        },
    )
    assert snapshot.clean(tmp_path) == {"CHANGELOG.md": 2, ".changeset": 1}
    assert [p.name for p in tmp_path.rglob("*") if p.is_file()] == ["changelog.ts"]


def test_nearest_rank_percentile():
    assert snapshot.nearest_rank([5, 1, 3, 2, 4, 6, 7, 8, 9, 10], 90) == 9
    assert snapshot.nearest_rank([7], 90) == 7
    assert snapshot.median([1, 2, 3, 4]) == 2.5
    assert snapshot.median([1, 2, 3]) == 2


def issue_root(tmp_path: Path) -> Path:
    shutil.copytree(
        CASES, tmp_path / "benchmark" / "cases", ignore=shutil.ignore_patterns("results")
    )
    return tmp_path


def fake(url: str, body: str = "Steps\r\n\r\n1. run\r\n", **extra):
    calls = []

    def fetch(api_url):
        calls.append(api_url)
        return {
            "html_url": url,
            "title": "Last unit sold twice",
            "body": body,
            "updated_at": "2026-10-18T01:41:26Z",
            **extra,
        }

    return fetch, calls


def test_issue_snapshot(tmp_path, monkeypatch):
    root = issue_root(tmp_path)
    monkeypatch.setattr(snapshot, "now", lambda: "2026-10-28T00:00:00+00:00")
    url = "https://github.com/medusajs/medusa/issues/17032"
    fetch, calls = fake(url)
    record = snapshot.build_issue("medusa-17032-last-unit", root, fetch)
    assert calls == ["https://api.github.com/repos/medusajs/medusa/issues/17032"]
    text = (root / "snapshots/issues/medusa-17032-last-unit.md").read_text()
    assert text == (
        "# Last unit sold twice\n\n"
        f"Issue: {url}\n"
        "Fetched: 2026-10-28T00:00:00+00:00\n\n"
        "Steps\n\n1. run\n"
    )
    assert record == {
        "url": url,
        "title": "Last unit sold twice",
        "issue_updated_at": "2026-10-18T01:41:26Z",
        "fetched": "2026-10-28T00:00:00+00:00",
        "characters": len(text),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    index = json.loads((root / "benchmark/snapshots/issues.json").read_text())
    assert index == {"schema": snapshot.ISSUES_SCHEMA, "issues": {"medusa-17032-last-unit": record}}
    assert "1. run" not in (root / "benchmark/snapshots/issues.json").read_text()


def test_issue_index_keeps_other_cases(tmp_path):
    root = issue_root(tmp_path)
    fetch, _ = fake("https://github.com/medusajs/medusa/issues/17032")
    snapshot.build_issue("medusa-17032-last-unit", root, fetch)
    snapshot.build_issue("medusa-17032-counter", root, fetch)
    index = json.loads((root / "benchmark/snapshots/issues.json").read_text())
    assert list(index["issues"]) == ["medusa-17032-counter", "medusa-17032-last-unit"]


def test_issue_snapshot_refuses_pull_requests_and_other_urls(tmp_path):
    root = issue_root(tmp_path)
    url = "https://github.com/medusajs/medusa/issues/17032"
    fetch, _ = fake(url, pull_request={"url": "x"})
    with pytest.raises(ValueError, match="pull request"):
        snapshot.build_issue("medusa-17032-last-unit", root, fetch)
    fetch, _ = fake("https://github.com/medusajs/medusa/issues/1")
    with pytest.raises(ValueError, match="expected"):
        snapshot.build_issue("medusa-17032-last-unit", root, fetch)
    with pytest.raises(ValueError, match="kebab-case"):
        snapshot.build_issue("../x", root, fetch)
    assert not (root / "snapshots").exists()


def test_committed_manifests_cover_every_case_version():
    versions = {v for case in CASES.iterdir() for v in load_case(case).versions}
    found = {p.stem.removeprefix("medusa-") for p in SNAPSHOTS.glob("medusa-*.json")}
    assert found == versions
    for v in versions:
        text = (SNAPSHOTS / f"medusa-{v}.json").read_text()
        m = json.loads(text)
        assert list(m) == FIELDS
        assert m["version"] == v and m["tag"] == f"v{v}"
        assert re.fullmatch(r"[0-9a-f]{40}", m["commit"])
        assert re.fullmatch(r"[0-9a-f]{64}", m["sha256"])
        assert m["repo"] == snapshot.MEDUSA_REPO
        assert m["folders"] == ["packages"]
        assert m["files"] > 0 and m["bytes"] > 0
        home = os.path.expanduser("~")
        assert home not in text and os.path.dirname(home) + "/" not in text


def test_committed_issue_index_covers_every_case():
    index = json.loads((SNAPSHOTS / "issues.json").read_text())
    assert index["schema"] == snapshot.ISSUES_SCHEMA
    assert sorted(index["issues"]) == sorted(p.name for p in CASES.iterdir())
    for case_id, record in index["issues"].items():
        assert record["url"] == load_case(CASES / case_id).issue.url
        assert set(record) == {
            "url",
            "title",
            "issue_updated_at",
            "fetched",
            "characters",
            "sha256",
        }
