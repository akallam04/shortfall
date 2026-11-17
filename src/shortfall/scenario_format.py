from dataclasses import dataclass

import yaml

VERSION = "2.22.0"
WILDCARD = "<name>"


@dataclass(frozen=True)
class Field:
    path: str
    type: str
    required: bool
    rule: str


FIELDS = (
    Field("schema", "string", True, "Must be `oversold.scenario/v1`."),
    Field(
        "name",
        "string",
        True,
        "Kebab-case: lowercase letters, digits and single dashes, at most 64 characters. "
        "The harness replaces it with its own name.",
    ),
    Field("description", "string", True, "Plain text. Not empty."),
    Field("target.engine", "string", True, "Only `medusa`."),
    Field("target.version", "string", True, f"Only `{VERSION}`. The harness sets it."),
    Field(
        "target.servers",
        "integer",
        True,
        "`1` or `2`. With 2, a second Medusa server runs on the same database.",
    ),
    Field(
        "stock",
        "map",
        False,
        "Inventory SKU to stocked quantity, from 0 to 1000000. Keys are `WIDGET` or `SOLO`. "
        "Applied after the reset through the Admin API. Items not listed keep their seeded stock.",
    ),
    Field(
        "stock_before_race",
        "map",
        False,
        "Inventory SKU to stocked quantity, from 0 to 1000000, with the same keys as `stock`. "
        "Applied through the Admin API after every cart is prepared and before the race starts, "
        "so a cart can be built against one stock level and completed against another. "
        "An empty map, or the field with no value, is an error.",
    ),
    Field("carts", "map", True, "Cart name (kebab-case) to a cart. At least one cart."),
    Field(
        "carts.<name>.server",
        "integer",
        True,
        "The server the cart is built on, from 1 to `target.servers`.",
    ),
    Field(
        "carts.<name>.count",
        "integer",
        False,
        "From 1 to 100, default 1. With a count of N above 1, the scenario gets N identical "
        "carts named `<name>-1` to `<name>-N`, all on the cart's server.",
    ),
    Field("carts.<name>.lines", "list", True, "At least one line."),
    Field(
        "carts.<name>.lines[].sku",
        "string",
        True,
        "A variant SKU from the catalog below. A SKU may appear once per cart.",
    ),
    Field("carts.<name>.lines[].qty", "integer", True, "From 1 to 1000."),
    Field("race", "list", True, "At least one action."),
    Field("race[].id", "string", True, "Kebab-case, unique in the scenario."),
    Field(
        "race[].server",
        "integer",
        True,
        "The server the action is sent to, from 1 to `target.servers`.",
    ),
    Field(
        "race[].do",
        "string",
        True,
        "Only `complete`. Sends `POST /store/carts/{id}/complete`.",
    ),
    Field(
        "race[].cart",
        "string",
        True,
        "A cart name from `carts`. Two actions may name the same cart. An action on a cart "
        "with a count of N above 1 becomes N actions, ids `<id>-1` to `<id>-N`, one per copy.",
    ),
    Field(
        "timing.release",
        "string",
        True,
        "`together`: every race action is released at once. `sequential`: actions run one "
        "after another in the listed order, each waiting for the previous response.",
    ),
    Field(
        "timing.jitter_ms",
        "[min, max]",
        False,
        "Extra delay before each race action, drawn from a seeded random source. "
        "`0 <= min <= max <= 10000`. Default: no delay.",
    ),
    Field(
        "timing.request_timeout_ms",
        "integer",
        False,
        "Timeout for every HTTP request in the run, from 100 to 120000. Default 30000.",
    ),
    Field("faults", "list", False, "Must be empty or absent."),
    Field(
        "runs",
        "integer",
        True,
        "From 1 to 1000. The harness decides how many runs each attempt gets.",
    ),
    Field(
        "seed",
        "integer",
        True,
        "Seeds the jitter. The same seed and run index always give the same delays.",
    ),
)

REFUSED = {
    "checks": "a candidate may not set checks, every run uses every check",
    "target.variant": "a candidate may not set target.variant, only the harness sets it",
    "target.locking": "a candidate may not set target.locking, only the harness sets it",
}

CATALOG = (
    ("OVS-PIECE", "WIDGET", 1, "10, shared"),
    ("OVS-TWOPACK", "WIDGET", 2, "10, shared"),
    ("OVS-SOLO", "SOLO", 1, "1"),
)

CHECKS = (
    (
        "no_oversell",
        "Live reservations never exceed stock, and the run's orders never need more units "
        "than were stocked at the start of the race.",
    ),
    (
        "reserved_matches_reservations",
        "The reserved quantity on each inventory level equals the sum of its live reservations.",
    ),
    (
        "one_order_per_cart",
        "A cart is linked to at most one order, and every `ok` complete call for a cart "
        "returned the same order.",
    ),
    (
        "no_orphaned_orders",
        "Every order comes from a scenario cart and holds the reservations its lines need, "
        "and a cart whose completion definitely failed has no order.",
    ),
    (
        "no_missing_orders",
        "Every `ok` complete call returned the id of exactly one saved order that is not "
        "canceled and is linked to that cart. A cart with an `unknown` complete call is skipped.",
    ),
)
CHECK_NAMES = tuple(name for name, _ in CHECKS)

EXAMPLE = {
    "schema": "oversold.scenario/v1",
    "name": "two-carts-one-server",
    "description": "Two carts each hold one SOLO unit and are completed together on one server.",
    "target": {"engine": "medusa", "version": VERSION, "servers": 1},
    "stock": {"SOLO": 1},
    "carts": {
        "alice": {"server": 1, "lines": [{"sku": "OVS-SOLO", "qty": 1}]},
        "bob": {"server": 1, "lines": [{"sku": "OVS-SOLO", "qty": 1}]},
    },
    "race": [
        {"id": "alice-completes", "server": 1, "do": "complete", "cart": "alice"},
        {"id": "bob-completes", "server": 1, "do": "complete", "cart": "bob"},
    ],
    "timing": {"release": "together", "jitter_ms": [0, 3]},
    "faults": [],
    "runs": 10,
    "seed": 1,
}

STEPS = (
    "The database is reset to a fresh copy with the seeded catalog and stock, and the servers "
    "restart, which clears their in-memory state.",
    "Stock from `stock` is set through the Admin API.",
    "Each cart is prepared on its server: lines, email, address, shipping method and payment "
    "session. If `stock_before_race` is set, that stock is applied next.",
    "A database snapshot is taken.",
    "The race actions are released as `timing.release` says.",
    "After a fixed 2-second wait, a second snapshot is taken and every check judges the run.",
)


def tree() -> dict:
    root: dict = {}
    for f in FIELDS:
        node = root
        for part in f.path.split("."):
            node = node.setdefault(part, {})
    return root


def unknown_fields(data, node: dict | None = None, prefix: str = "") -> list[str]:
    node = tree() if node is None else node
    if not isinstance(data, dict):
        return []
    found = []
    for key, value in data.items():
        key = str(key)
        if WILDCARD in node:
            child, path = node[WILDCARD], f"{prefix}{key}"
        elif f"{key}[]" in node:
            child = node[f"{key}[]"]
            if isinstance(value, list):
                for item in value:
                    found += unknown_fields(item, child, f"{prefix}{key}[].")
            continue
        elif key in node:
            child, path = node[key], f"{prefix}{key}"
        else:
            found.append(f"{prefix}{key}")
            continue
        if child:
            found += unknown_fields(value, child, f"{path}.")
    return found


def refused_fields(data) -> list[str]:
    if not isinstance(data, dict):
        return []
    found = ["checks"] if "checks" in data else []
    target = data.get("target")
    if isinstance(target, dict):
        found += [f"target.{key}" for key in ("variant", "locking") if key in target]
    return found


def format_text() -> str:
    rows = [
        f"| `{f.path}` | {f.type} | {'yes' if f.required else 'no'} | {f.rule} |" for f in FIELDS
    ]
    catalog = [
        f"| `{sku}` | `{item}` | {units} | {seeded} |" for sku, item, units, seeded in CATALOG
    ]
    checks = [f"| `{name}` | {meaning} |" for name, meaning in CHECKS]
    steps = [f"{n}. {text}" for n, text in enumerate(STEPS, start=1)]
    example = yaml.safe_dump(EXAMPLE, sort_keys=False, default_flow_style=False, width=88)
    return (
        "\n".join(
            [
                "# Scenario format",
                "",
                "A scenario is one YAML file that says how to set up stock and carts, which "
                "requests to race, and how to time them.",
                "",
                "Decoding is strict. The file holds exactly one YAML document, and a field that "
                "is not listed below is refused, at any level.",
                "",
                "| Field | Type | Required | Rules |",
                "|---|---|---|---|",
                *rows,
                "",
                "Carts are prepared in the order they appear in the file. After expanding counts, "
                "cart names and action ids must still be unique, and a scenario may have at most "
                "200 race actions.",
                "",
                "## Catalog",
                "",
                "The seed creates a fixed catalog. Scenarios can only use these SKUs.",
                "",
                "| Variant SKU | Inventory item | Units of the item per unit ordered "
                "| Seeded stock |",
                "|---|---|---|---|",
                *catalog,
                "",
                "## Checks",
                "",
                "Every run is judged by all five checks below. A scenario cannot choose, skip or "
                "change them. The check rules give each one's exact definition.",
                "",
                "| Name | Meaning |",
                "|---|---|",
                *checks,
                "",
                "## What one run does",
                "",
                *steps,
                "",
                "A setup call that does not succeed makes the run inconclusive.",
                "",
                "## Example",
                "",
                "```yaml",
                example.rstrip(),
                "```",
            ]
        )
        + "\n"
    )


KEEP_SECTIONS = ("Terms", "Inconclusive runs", *CHECK_NAMES)


def check_rules_text(source: str) -> str:
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in source.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), [line]))
        else:
            sections[-1][1].append(line)
    out = [
        "# Checks",
        "",
        "A check reads one run's saved history and gives a verdict: `pass`, `fail` or "
        "`inconclusive`. Every run is judged by all five checks: "
        + ", ".join(CHECK_NAMES[:-1])
        + f" and {CHECK_NAMES[-1]}. A scenario cannot choose, skip or change them.",
        "",
    ]
    for title, lines in sections[1:]:
        if title.split(" ")[0] in KEEP_SECTIONS or title in KEEP_SECTIONS:
            out += lines
    return "\n".join(out).rstrip() + "\n"
