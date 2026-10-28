import os
import re
from pathlib import Path

MAX_CHARS = 40_000
MAX_LINES = 400
MAX_MATCHES = 50
MAX_MATCH_LINE = 300
BINARY_PROBE = 8192

_DRIVE = re.compile(r"[A-Za-z]:")
_SEP = re.compile(r"[\\/]")


class ToolError(ValueError):
    pass


def cut(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return text
    note = f"\n[cut at {MAX_CHARS} characters, the full result was {len(text)} characters]"
    return text[: MAX_CHARS - len(note)] + note


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:BINARY_PROBE]


def lines_of(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="replace")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line.removesuffix("\r") for line in lines]


def real_path(p: Path) -> Path | None:
    try:
        return p.resolve()
    except (OSError, RuntimeError):
        return None


class Snapshot:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError(f"{root} is not a folder")

    def _inside(self, real: Path) -> bool:
        return real == self.root or self.root in real.parents

    def _resolve(self, path: str) -> tuple[Path, str]:
        if not isinstance(path, str):
            raise ToolError("path must be text")
        if "\0" in path:
            raise ToolError("path must not contain a NUL character")
        if path.startswith(("/", "\\", "~")) or _DRIVE.match(path) or os.path.isabs(path):
            raise ToolError(f"{path}: absolute paths are not allowed")
        parts = [p for p in _SEP.split(path) if p not in ("", ".")]
        if ".." in parts:
            raise ToolError(f"{path}: '..' is not allowed, give a path inside the snapshot")
        real = real_path(self.root.joinpath(*parts))
        if real is None or not self._inside(real):
            raise ToolError(f"{path}: points outside the snapshot")
        if not real.exists():
            raise ToolError(f"{path}: not found")
        return real, "/".join(parts) or "."

    def _read(self, real: Path, shown: str) -> bytes:
        try:
            data = real.read_bytes()
        except OSError as err:
            raise ToolError(f"{shown}: cannot be read ({err.strerror})") from None
        return data

    def list_files(self, path: str = ".") -> str:
        real, shown = self._resolve(path)
        if not real.is_dir():
            raise ToolError(f"{shown}: not a folder")
        rows = []
        folders = files = 0
        for entry in sorted(os.scandir(real), key=lambda e: e.name):
            if entry.is_symlink():
                target = real_path(Path(entry.path))
                if target is not None and not self._inside(target):
                    rows.append(f"{entry.name} (link outside the snapshot)")
                elif target is None or not target.exists():
                    rows.append(f"{entry.name} (broken link)")
                elif target.is_dir():
                    rows.append(f"{entry.name}/")
                    folders += 1
                else:
                    rows.append(f"{entry.name} ({target.stat().st_size} bytes)")
                    files += 1
            elif entry.is_dir():
                rows.append(f"{entry.name}/")
                folders += 1
            else:
                rows.append(f"{entry.name} ({entry.stat().st_size} bytes)")
                files += 1
        head = f"{shown}: {folders} folders, {files} files"
        return cut("\n".join([head, *rows]) if rows else f"{head}\n(empty)")

    def read_file(self, path: str, start: int = 1, end: int | None = None) -> str:
        if type(start) is not int or start < 1:
            raise ToolError("start must be a whole number from 1")
        if end is not None and (type(end) is not int or end < start):
            raise ToolError("end must be a whole number not below start")
        real, shown = self._resolve(path)
        if not real.is_file():
            raise ToolError(f"{shown}: not a file")
        data = self._read(real, shown)
        if is_binary(data):
            raise ToolError(f"{shown}: binary file, not shown")
        lines = lines_of(data)
        total = len(lines)
        if total == 0:
            return f"{shown}: empty file"
        if start > total:
            raise ToolError(f"{shown} has {total} lines, start {start} is past the end")
        wanted = end if end is not None else start + MAX_LINES - 1
        last = min(wanted, start + MAX_LINES - 1, total)
        rows = [f"{shown}, lines {start} to {last} of {total}"]
        rows += [f"{n:6d}\t{lines[n - 1]}" for n in range(start, last + 1)]
        if last < min(wanted, total):
            rows.append(f"[at most {MAX_LINES} lines per call, read on with start={last + 1}]")
        elif last < total and end is None:
            rows.append(f"[{total - last} more lines, read on with start={last + 1}]")
        return cut("\n".join(rows))

    def _files(self, real: Path):
        if real.is_file():
            yield real
            return
        for dirpath, dirnames, filenames in os.walk(real):
            dirnames.sort()
            for name in sorted(filenames):
                p = Path(dirpath) / name
                if p.is_symlink():
                    target = real_path(p)
                    if target is None or not self._inside(target) or not target.is_file():
                        continue
                yield p

    def search(self, text: str, path: str = ".") -> str:
        if not isinstance(text, str) or text == "":
            raise ToolError("text must be a non-empty string")
        if "\n" in text or "\r" in text:
            raise ToolError("text must be on one line")
        real, shown = self._resolve(path)
        matches = []
        more = False
        for p in self._files(real):
            try:
                data = p.read_bytes()
            except OSError:
                continue
            if is_binary(data) or text.encode() not in data:
                continue
            rel = p.relative_to(self.root).as_posix()
            for n, line in enumerate(lines_of(data), 1):
                if text in line:
                    if len(matches) == MAX_MATCHES:
                        more = True
                        break
                    line = line.strip()
                    if len(line) > MAX_MATCH_LINE:
                        line = line[:MAX_MATCH_LINE] + "..."
                    matches.append(f"{rel}:{n}: {line}")
            if more:
                break
        if not matches:
            return f"no matches for {text!r} under {shown}"
        head = f"{len(matches)} matches for {text!r} under {shown}"
        if more:
            head = f"first {MAX_MATCHES} matches for {text!r} under {shown}"
        rows = [head, *matches]
        if more:
            rows.append(f"[stopped at {MAX_MATCHES} matches, narrow the path or the text]")
        return cut("\n".join(rows))
