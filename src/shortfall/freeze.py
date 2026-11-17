import argparse
import hashlib
import json
import sys
from pathlib import Path

from shortfall import agent, models

HASH_FILE = Path("benchmark") / "agent" / "prompts.sha256"
COVERS = (
    ("src/shortfall/prompts/system.md", "system prompt"),
    ("src/shortfall/prompts/setup.md", "description of the test setup"),
    ("src/shortfall/prompts/guided.md", "guided task text"),
    ("src/shortfall/prompts/unguided.md", "unguided task text"),
    ("benchmark/causes.yaml", "causes list"),
    ("src/shortfall/scenario_format.py", "scenario format text and check rules filter"),
    (".oversold/docs/checks.md", "check rules, from the pinned Oversold commit"),
    (
        "src/shortfall/agent.py",
        "tool definitions, feedback templates, opening layout, history shortening, "
        "read and result limits",
    ),
    ("src/shortfall/models.py", "max_tokens and thinking settings"),
)


def issue_files(root: Path) -> list[Path]:
    return sorted((Path(root) / "snapshots" / "issues").glob("*.md"))


def manifest(root: Path) -> dict:
    root = Path(root)
    terms = agent.forbidden_terms(root / "benchmark" / "cases")
    return {
        "unguided": agent.opening(root, "unguided", None, terms),
        "guided": {p.stem: agent.opening(root, "guided", p.stem, terms) for p in issue_files(root)},
        "tools": agent.TOOLS,
        "feedback": agent.FEEDBACK,
        "settings": {
            "keep_turns": agent.KEEP_TURNS,
            "read_lines": agent.READ_LINES,
            "result_chars": agent.RESULT_CHARS,
            "hypothesis_chars": agent.HYPOTHESIS_CHARS,
            "max_claims": agent.MAX_CLAIMS,
            "model_retries": agent.MODEL_RETRIES,
            "max_tokens": models.MAX_TOKENS,
            "thinking": {name: spec.thinking for name, spec in sorted(models.MODELS.items())},
        },
    }


def prompt_hash(root: Path) -> str:
    text = json.dumps(manifest(root), sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def hash_file_text(root: Path) -> str:
    root = Path(root)
    lines = [
        prompt_hash(root),
        "",
        "This sha256 covers everything the agent is shown and the loop settings,",
        "taken from these files:",
        "",
    ]
    lines += [f"- {path}: {what}" for path, what in COVERS]
    lines += ["", "and the bug reports shown in guided mode, kept outside the repo:", ""]
    for p in issue_files(root):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"- snapshots/issues/{p.name}: sha256 {digest}")
    return "\n".join(lines) + "\n"


def recorded_hash(root: Path) -> str | None:
    path = Path(root) / HASH_FILE
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").splitlines()[0].strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.freeze")
    p.add_argument("command", choices=("write", "check", "print"))
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if args.command == "write":
        (root / HASH_FILE).parent.mkdir(parents=True, exist_ok=True)
        (root / HASH_FILE).write_text(hash_file_text(root), encoding="utf-8")
        print(recorded_hash(root))
        return 0
    current = prompt_hash(root)
    if args.command == "print":
        print(current)
        return 0
    recorded = recorded_hash(root)
    if recorded != current:
        print(f"prompt hash {current} differs from the recorded {recorded}")
        return 1
    print(f"prompt hash {current} matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
