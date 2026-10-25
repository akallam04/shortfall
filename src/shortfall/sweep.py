import argparse
import datetime
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

SKUS = {
    "OVS-PIECE": ("WIDGET", 1),
    "OVS-TWOPACK": ("WIDGET", 2),
    "OVS-SOLO": ("SOLO", 1),
}
MAX_STOCK = 1000000
MAX_NAME = 56
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")

GRID_SERVERS = (2, 1)
GRID_LINES = (
    ("solo", (("OVS-SOLO", 1),)),
    ("piece", (("OVS-PIECE", 1),)),
    ("piece-twopack", (("OVS-PIECE", 1), ("OVS-TWOPACK", 1))),
)
GRID_CARTS = (2, 10)
GRID_STOCK = ("under", "short", "ample")
GRID_SEQUENTIAL_LINES = ("solo", "piece-twopack")


@dataclass(frozen=True)
class Group:
    server: int
    count: int
    lines: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Candidate:
    name: str
    description: str
    version: str
    servers: int
    groups: tuple[Group, ...]
    stock: tuple[tuple[str, int], ...]
    release: str
    seed: int


def cart_demand(lines) -> dict[str, int]:
    demand: dict[str, int] = {}
    for sku, qty in lines:
        item, units = SKUS[sku]
        demand[item] = demand.get(item, 0) + units * qty
    return demand


def total_demand(groups) -> dict[str, int]:
    total: dict[str, int] = {}
    for group in groups:
        for item, units in cart_demand(group.lines).items():
            total[item] = total.get(item, 0) + units * group.count
    return total


def split_groups(servers: int, carts: int, lines) -> tuple[Group, ...]:
    if servers == 1:
        return (Group(server=1, count=carts, lines=lines),)
    first = carts - carts // 2
    return (
        Group(server=1, count=first, lines=lines),
        Group(server=2, count=carts - first, lines=lines),
    )


def grid_stock(level: str, groups) -> tuple[tuple[str, int], ...]:
    stock = []
    for item, total in sorted(total_demand(groups).items()):
        one = max(cart_demand(g.lines).get(item, 0) for g in groups)
        if level == "under":
            value = one - 1
            biggest_line = max(
                SKUS[sku][1] * qty for g in groups for sku, qty in g.lines if SKUS[sku][0] == item
            )
            if value < biggest_line:
                raise ValueError(f"under stock for {item} is below a single line's need")
        elif level == "short":
            value = max(total - one, 0)
        elif level == "ample":
            value = min(total * 10, MAX_STOCK)
        else:
            raise ValueError(f"unknown stock level {level}")
        stock.append((item, value))
    return tuple(stock)


def lines_text(lines) -> str:
    return " and ".join(f"{sku} {qty}" for sku, qty in lines)


def describe(label: str, servers: int, groups, stock, release) -> str:
    carts = sum(g.count for g in groups)
    parts = [f"{g.count} on server {g.server} holding {lines_text(g.lines)}" for g in groups]
    stock_text = ", ".join(f"{item} {value}" for item, value in stock)
    when = "together" if release == "together" else "one after another"
    server_text = "1 server" if servers == 1 else f"{servers} servers"
    cart_text = "1 cart" if carts == 1 else f"{carts} carts"
    return (
        f"Sweep {label}. {server_text}, {cart_text}: {'; '.join(parts)}. "
        f"Stock: {stock_text}. Completions released {when}."
    )


def grid(seed: int = 0, version: str = "2.21.2") -> list[Candidate]:
    combos = []
    for servers in GRID_SERVERS:
        for shape, lines in GRID_LINES:
            for carts in GRID_CARTS:
                for level in GRID_STOCK:
                    if level == "under" and len(lines) < 2:
                        continue
                    combos.append((servers, shape, lines, carts, level, "together"))
    for servers in GRID_SERVERS:
        for shape, lines in GRID_LINES:
            if shape in GRID_SEQUENTIAL_LINES:
                combos.append((servers, shape, lines, 2, "short", "sequential"))
    candidates = []
    for index, (servers, shape, lines, carts, level, release) in enumerate(combos, start=1):
        groups = split_groups(servers, carts, lines)
        stock = grid_stock(level, groups)
        name = f"grid-{index:03d}-s{servers}-{shape}-c{carts}-{level}-{release}"
        candidates.append(
            Candidate(
                name=name,
                description=describe(f"grid candidate {index}", servers, groups, stock, release),
                version=version,
                servers=servers,
                groups=groups,
                stock=stock,
                release=release,
                seed=seed + index,
            )
        )
    return candidates


def random_candidates(seed: int, count: int = 20, version: str = "2.21.2") -> list[Candidate]:
    if count < 1:
        raise ValueError("count must be 1 or more")
    rng = random.Random(seed)
    skus = sorted(SKUS)
    candidates = []
    for index in range(1, count + 1):
        servers = rng.choice((1, 2))
        n_groups = 2 if servers == 2 else rng.choice((1, 2))
        groups = []
        for g in range(n_groups):
            n_lines = rng.choice((1, 2))
            chosen = sorted(rng.sample(skus, n_lines))
            lines = tuple((sku, rng.randint(1, 3)) for sku in chosen)
            groups.append(Group(server=min(g + 1, servers), count=rng.randint(1, 10), lines=lines))
        if rng.random() < 0.5:
            groups.reverse()
        groups = tuple(groups)
        stock = tuple(
            (item, rng.randint(0, min(2 * total, MAX_STOCK)))
            for item, total in sorted(total_demand(groups).items())
        )
        release = rng.choice(("together", "sequential"))
        name = f"random-{index:03d}-s{servers}"
        candidates.append(
            Candidate(
                name=name,
                description=describe(f"random candidate {index}", servers, groups, stock, release),
                version=version,
                servers=servers,
                groups=groups,
                stock=stock,
                release=release,
                seed=rng.randrange(1, 1000000),
            )
        )
    return candidates


def cart_names(groups) -> list[str]:
    if len(groups) == 1:
        return ["buyer"]
    return [f"buyer-{chr(ord('a') + i)}" for i in range(len(groups))]


def to_data(candidate: Candidate) -> dict:
    names = cart_names(candidate.groups)
    carts = {}
    race = []
    for name, group in zip(names, candidate.groups, strict=True):
        cart = {"server": group.server}
        if group.count > 1:
            cart["count"] = group.count
        cart["lines"] = [{"sku": sku, "qty": qty} for sku, qty in group.lines]
        carts[name] = cart
        race.append(
            {
                "id": name.replace("buyer", "complete"),
                "server": group.server,
                "do": "complete",
                "cart": name,
            }
        )
    return {
        "schema": "oversold.scenario/v1",
        "name": candidate.name,
        "description": candidate.description,
        "target": {
            "engine": "medusa",
            "version": candidate.version,
            "servers": candidate.servers,
        },
        "stock": dict(candidate.stock),
        "carts": carts,
        "race": race,
        "timing": {"release": candidate.release},
        "faults": [],
        "runs": 10,
        "seed": candidate.seed,
    }


def to_yaml(candidate: Candidate) -> str:
    if len(candidate.name) > MAX_NAME:
        raise ValueError(f"name {candidate.name!r} is over {MAX_NAME} characters")
    return yaml.safe_dump(
        to_data(candidate), sort_keys=False, default_flow_style=False, allow_unicode=True, width=80
    )


def write(candidates: list[Candidate], out_dir: str | Path) -> list[Path]:
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError(f"{out_dir} is not empty")
    names = [c.name for c in candidates]
    if len(set(names)) != len(names):
        raise ValueError("candidate names must be unique")
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for candidate in candidates:
        path = out_dir / f"{candidate.name}.yaml"
        path.write_text(to_yaml(candidate), encoding="utf-8")
        paths.append(path)
    return paths


def repo_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    if not (root / "oversold.lock").is_file():
        raise RuntimeError("cannot find the repo root next to the shortfall package")
    return root


def parse_args(argv):
    p = argparse.ArgumentParser(prog="python -m shortfall.sweep")
    p.add_argument("--mode", choices=("grid", "random"), default="grid")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--count", type=int, default=20, help="candidates in random mode")
    p.add_argument("--version", default="2.21.2")
    p.add_argument("--max-runs", type=int, help="override the session cap on Oversold runs")
    p.add_argument(
        "--raise-dollar-cap",
        type=float,
        metavar="USD",
        help="raise the dollar cap above its default of 0",
    )
    p.add_argument("--generate-only", action="store_true")
    p.add_argument("--rerun", metavar="ATTEMPT_ID", help="rerun one attempt from the ledger")
    args = p.parse_args(argv)
    if not VERSION.fullmatch(args.version):
        p.error("--version must look like 2.21.2")
    if args.max_runs is not None and args.max_runs < 1:
        p.error("--max-runs must be 1 or more")
    if args.raise_dollar_cap is not None and args.raise_dollar_cap < 0:
        p.error("--raise-dollar-cap must be 0 or more")
    return args


def main(argv=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = repo_root()
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")

    from shortfall import score

    if args.rerun:
        return score.rerun(root, args.rerun, stamp, args.max_runs, args.raise_dollar_cap)

    if args.mode == "grid":
        candidates = grid(args.seed, args.version)
    else:
        candidates = random_candidates(args.seed, args.count, args.version)
    out_dir = root / "runs" / "sweep" / stamp
    paths = write(candidates, out_dir)
    print(f"sweep: wrote {len(paths)} {args.mode} candidates to runs/sweep/{stamp}")
    if args.generate_only:
        return 0
    return score.run_sweep(
        root, paths, args.version, args.seed, stamp, args.max_runs, args.raise_dollar_cap
    )


if __name__ == "__main__":
    sys.exit(main())
