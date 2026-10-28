import argparse
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path

from shortfall.cases import load_case

MEDUSA_REPO = "https://github.com/medusajs/medusa.git"
FOLDER = "packages"
SCHEMA = "shortfall.snapshot/v1"
ISSUES_SCHEMA = "shortfall.issues/v1"
_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_ISSUE_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/issues/([1-9][0-9]*)"
)
_CASE_ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


GUIDE_REASON = (
    "guides written for AI coding tools; only 2.22.0 ships them, so keeping them would give "
    "the 2.22.0 agent hints the other versions don't get"
)
REMOVED_FILES = {
    "CHANGELOG.md": "release history, which the agent does not read",
    "AGENTS.md": GUIDE_REASON,
    "CLAUDE.md": GUIDE_REASON,
}
REMOVED_FOLDERS = {".changeset": "notes on unreleased changes, which the agent does not read"}


def clean(folder: Path) -> list[dict]:
    counts = dict.fromkeys([*REMOVED_FILES, *REMOVED_FOLDERS], 0)
    by_lower = {name.lower(): name for name in REMOVED_FILES}
    for dirpath, dirnames, filenames in os.walk(folder):
        for d in sorted(dirnames):
            if d in REMOVED_FOLDERS:
                shutil.rmtree(Path(dirpath) / d)
                dirnames.remove(d)
                counts[d] += 1
        for f in filenames:
            name = by_lower.get(f.lower())
            if name:
                (Path(dirpath) / f).unlink()
                counts[name] += 1
    return [
        {"name": name, "kind": kind, "count": counts[name], "reason": reason}
        for kind, table in (("file", REMOVED_FILES), ("folder", REMOVED_FOLDERS))
        for name, reason in table.items()
    ]


def entries(folder: Path) -> list[tuple[str, Path]]:
    out = []
    for dirpath, dirnames, filenames in os.walk(folder):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            if name in filenames or p.is_symlink():
                out.append((p.relative_to(folder).as_posix(), p))
    return sorted(out)


def file_hash(p: Path) -> tuple[str, int]:
    if p.is_symlink():
        data = b"link:" + os.readlink(p).encode()
        return hashlib.sha256(data).hexdigest(), 0
    h = hashlib.sha256()
    size = 0
    with p.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def nearest_rank(values: list[int], pct: int) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct / 100 * len(ordered)) - 1)]


def median(values: list[int]) -> int | float:
    m = statistics.median(values)
    return int(m) if m == int(m) else m


def manifest(folder: Path) -> dict:
    total = hashlib.sha256()
    count = 0
    size = 0
    links = 0
    ts_chars = []
    for rel, p in entries(folder):
        digest, n = file_hash(p)
        total.update(f"{digest}  {rel}\n".encode())
        count += 1
        size += n
        if p.is_symlink():
            links += 1
        elif rel.endswith(".ts"):
            ts_chars.append(len(p.read_bytes().decode("utf-8", errors="replace")))
    return {
        "files": count,
        "links": links,
        "bytes": size,
        "sha256": total.hexdigest(),
        "ts_files": {
            "count": len(ts_chars),
            "median_chars": median(ts_chars) if ts_chars else 0,
            "p90_chars": nearest_rank(ts_chars, 90) if ts_chars else 0,
        },
    }


def git(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "core.symlinks=true", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed: {proc.stderr.strip()}")
    return proc.stdout


def remote_tag_commit(tag: str) -> str:
    out = git("ls-remote", MEDUSA_REPO, f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}")
    refs = dict(reversed(line.split("\t")) for line in out.splitlines() if line)
    commit = refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")
    if not commit:
        raise RuntimeError(f"tag {tag} not found in {MEDUSA_REPO}")
    return commit


def build_source(version: str, root: Path) -> tuple[dict, bool | None]:
    if not _VERSION.fullmatch(version):
        raise ValueError(f"version must look like 2.22.0, got {version!r}")
    tag = f"v{version}"
    snapshots = root / "snapshots"
    snapshots.mkdir(exist_ok=True)
    dest = snapshots / f"medusa-{version}"
    work = snapshots / f".build-medusa-{version}"
    if work.exists():
        shutil.rmtree(work)
    try:
        clone = work / "clone"
        git(
            "clone",
            "--quiet",
            "--depth",
            "1",
            "--branch",
            tag,
            "--filter=blob:none",
            "--sparse",
            MEDUSA_REPO,
            str(clone),
        )
        git("sparse-checkout", "set", "--cone", FOLDER, cwd=clone)
        commit = git("rev-parse", "HEAD", cwd=clone).strip()
        if not _COMMIT.fullmatch(commit):
            raise RuntimeError(f"unexpected commit {commit!r}")
        expected = remote_tag_commit(tag)
        if commit != expected:
            raise RuntimeError(f"clone is at {commit}, tag {tag} points to {expected}")
        out = work / f"medusa-{version}"
        out.mkdir()
        (clone / FOLDER).rename(out / FOLDER)
        removed = clean(out)
        record = {
            "schema": SCHEMA,
            "engine": "medusa",
            "version": version,
            "repo": MEDUSA_REPO,
            "tag": tag,
            "commit": commit,
            "folders": [FOLDER],
            "removed": removed,
            **manifest(out),
        }
        if dest.exists():
            shutil.rmtree(dest)
        out.rename(dest)
    finally:
        if work.exists():
            shutil.rmtree(work)
    path = root / "benchmark" / "snapshots" / f"medusa-{version}.json"
    same = None
    if path.exists():
        same = json.loads(path.read_text(encoding="utf-8")) == record
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record, same


def fetch_issue(api_url: str) -> dict:
    req = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "shortfall-snapshot",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def issue_text(url: str, fetched: str, title: str, body: str) -> str:
    body = body.replace("\r\n", "\n").strip()
    return f"# {title}\n\nIssue: {url}\nFetched: {fetched}\n\n{body}\n"


def build_issue(case_id: str, root: Path, fetch: Callable[[str], dict] = fetch_issue) -> dict:
    if not _CASE_ID.fullmatch(case_id):
        raise ValueError(f"case id must be kebab-case, got {case_id!r}")
    case = load_case(root / "benchmark" / "cases" / case_id)
    found = _ISSUE_URL.fullmatch(case.issue.url)
    if not found:
        raise ValueError(f"{case.issue.url} is not a GitHub issue URL")
    owner, repo, number = found.groups()
    data = fetch(f"https://api.github.com/repos/{owner}/{repo}/issues/{number}")
    if "pull_request" in data:
        raise ValueError(f"{case.issue.url} is a pull request, not an issue")
    if data.get("html_url") != case.issue.url:
        raise ValueError(f"fetched {data.get('html_url')!r}, expected {case.issue.url}")
    title = data["title"]
    fetched = now()
    text = issue_text(case.issue.url, fetched, title, data.get("body") or "")
    out = root / "snapshots" / "issues" / f"{case_id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    record = {
        "url": case.issue.url,
        "title": title,
        "issue_updated_at": data.get("updated_at"),
        "fetched": fetched,
        "characters": len(text),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    index = root / "benchmark" / "snapshots" / "issues.json"
    issues = {"schema": ISSUES_SCHEMA, "issues": {}}
    if index.exists():
        issues = json.loads(index.read_text(encoding="utf-8"))
    issues["issues"][case_id] = record
    issues["issues"] = dict(sorted(issues["issues"].items()))
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(json.dumps(issues, indent=2) + "\n", encoding="utf-8")
    return record


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.snapshot")
    sub = p.add_subparsers(dest="kind", required=True)
    s = sub.add_parser("source", help="snapshot Medusa's packages folder at a release tag")
    s.add_argument("version")
    i = sub.add_parser("issue", help="snapshot a case's issue title and opening post")
    i.add_argument("case_id")
    args = p.parse_args(argv)
    root = repo_root()
    if args.kind == "source":
        record, same = build_source(args.version, root)
        print(
            f"snapshot medusa {args.version}: tag {record['tag']} commit {record['commit']}, "
            f"{record['files']} files, {record['bytes']} bytes, sha256 {record['sha256']}"
        )
        if same is not None:
            print("manifest matches the previous one" if same else "manifest changed")
        return 0
    record = build_issue(args.case_id, root)
    print(
        f"issue {args.case_id}: {record['title']!r}, fetched {record['fetched']}, "
        f"{record['characters']} characters, sha256 {record['sha256']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
