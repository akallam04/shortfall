import json
from pathlib import Path

HELD_FILE = Path(".git") / "info" / "held-shapes"
HELD_NOTE = "held shape: "

ISSUE_17032 = "https://github.com/medusajs/medusa/issues/17032"
ISSUE_16502 = "https://github.com/medusajs/medusa/issues/16502"
ISSUE_16825 = "https://github.com/medusajs/medusa/issues/16825"

MANUAL_CHECK = frozenset({ISSUE_16825})
FIXES_16502 = frozenset({"pr-16961"})


def covering_issues(shape: dict, rule: str) -> tuple[str, ...]:
    issues = []
    in_memory = shape.get("locking", "in-memory") != "redis"
    if (
        in_memory
        and shape["servers"] == 2
        and rule in ("no_oversell", "reserved_matches_reservations")
    ):
        issues.append(ISSUE_17032)
    fixed_16502 = shape.get("variant") in FIXES_16502
    if rule == "no_oversell" and shape["item_on_several_lines"] and not fixed_16502:
        issues.append(ISSUE_16502)
        if in_memory and shape["carts"] > 1 and ISSUE_17032 not in issues:
            issues.append(ISSUE_17032)
    if rule == "no_orphaned_orders" and shape["carts"] > 1 and shape["release"] == "together":
        issues.append(ISSUE_16825)
    return tuple(issues)


def held_shapes(root: Path) -> list[dict]:
    path = Path(root) / HELD_FILE
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def race_steps(data: dict, keys: list[str]) -> list[str]:
    steps = [{k: step.get(k) for k in keys} for step in data.get("race") or []]
    return sorted(json.dumps(step, sort_keys=True) for step in steps)


def held_shape(root: Path, shape: dict, data: dict, rule: str) -> bool:
    for entry in held_shapes(root):
        if entry.get("rule") != rule:
            continue
        if any(shape.get(k) != v for k, v in (entry.get("shape") or {}).items()):
            continue
        race = entry.get("race")
        if race is not None:
            keys = sorted({k for step in race for k in step})
            want = sorted(
                json.dumps({k: step.get(k) for k in keys}, sort_keys=True) for step in race
            )
            if race_steps(data, keys) != want:
                continue
        return True
    return False
