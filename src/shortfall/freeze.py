import argparse
import hashlib
import json
import sys
from pathlib import Path

from shortfall import agent, models

HASH_FILE = Path("benchmark") / "agent" / "prompts.sha256"
PROMPT_VERSION = "v2"
HASH_FILES = {
    "v2": HASH_FILE,
    "v2-nomenu": Path("benchmark") / "agent" / "prompts-v2-nomenu.sha256",
    "v2-budget": Path("benchmark") / "agent" / "prompts-v2-budget.sha256",
}
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
    (
        "benchmark/snapshots/enterprise-2.22.0.json",
        "Enterprise Edition paths the tools refuse to show",
    ),
)


def issue_files(root: Path) -> list[Path]:
    return sorted((Path(root) / "snapshots" / "issues").glob("*.md"))


def manifest(root: Path, variant: str = "v2") -> dict:
    root = Path(root)
    terms = agent.forbidden_terms(root / "benchmark" / "cases")
    out = {
        "unguided": agent.opening(root, "unguided", None, terms, variant),
        "guided": {
            p.stem: agent.opening(root, "guided", p.stem, terms, variant) for p in issue_files(root)
        },
        "tools": agent.tools_for(variant),
        "feedback": agent.FEEDBACK,
        "settings": {
            "keep_turns": agent.KEEP_TURNS,
            "shorten_every": agent.SHORTEN_EVERY,
            "enterprise_paths": list(agent.enterprise_paths(root)),
            "read_lines": agent.READ_LINES,
            "result_chars": agent.RESULT_CHARS,
            "hypothesis_chars": agent.HYPOTHESIS_CHARS,
            "max_claims": agent.MAX_CLAIMS,
            "model_retries": agent.MODEL_RETRIES,
            "max_tokens": models.MAX_TOKENS,
            "thinking": {name: spec.thinking for name, spec in sorted(models.MODELS.items())},
        },
    }
    if variant != "v2":
        out["variant"] = variant
    if variant == agent.BUDGET:
        out["settings"]["finish_gate"] = {
            "runs_left_above": agent.GATE_RUNS,
            "text": agent.GATE_TEXT,
        }
    return out


def prompt_hash(root: Path, variant: str = "v2") -> str:
    text = json.dumps(
        manifest(root, variant), sort_keys=True, ensure_ascii=True, separators=(",", ":")
    )
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def covers(variant: str) -> tuple[tuple[str, str], ...]:
    if variant in ("v2", agent.BUDGET):
        return COVERS
    out = []
    for path, what in COVERS:
        if path == "benchmark/causes.yaml":
            continue
        if path == "src/shortfall/prompts/system.md":
            path, what = "src/shortfall/prompts/system-nomenu.md", "system prompt without causes"
        out.append((path, what))
    return tuple(out)


def hash_file_text(root: Path, variant: str = "v2") -> str:
    root = Path(root)
    version = PROMPT_VERSION if variant == "v2" else variant
    lines = [
        prompt_hash(root, variant),
        "",
        f"Prompt version {version}.",
        "",
        "This sha256 covers everything the agent is shown and the loop settings,",
        "taken from these files:",
        "",
    ]
    lines += [f"- {path}: {what}" for path, what in covers(variant)]
    lines += ["", "and the bug reports shown in guided mode, kept outside the repo:", ""]
    for p in issue_files(root):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"- snapshots/issues/{p.name}: sha256 {digest}")
    return "\n".join(lines) + "\n"


def recorded_hash(root: Path, variant: str = "v2") -> str | None:
    path = Path(root) / HASH_FILES[variant]
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").splitlines()[0].strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m shortfall.freeze")
    p.add_argument("command", choices=("write", "check", "print"))
    p.add_argument("--variant", choices=sorted(HASH_FILES), default="v2")
    args = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    target = root / HASH_FILES[args.variant]
    if args.command == "write":
        if target.exists():
            print(f"{target.name} exists and is frozen; remove it first to refreeze")
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(hash_file_text(root, args.variant), encoding="utf-8")
        print(recorded_hash(root, args.variant))
        return 0
    current = prompt_hash(root, args.variant)
    if args.command == "print":
        print(current)
        return 0
    recorded = recorded_hash(root, args.variant)
    if recorded != current:
        print(f"prompt hash {current} differs from the recorded {recorded}")
        return 1
    print(f"prompt hash {current} matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
