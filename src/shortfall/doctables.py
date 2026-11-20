import functools
import gzip
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

from shortfall import answers, ledger, score, stats
from shortfall.cases import load_case

CASES = ("medusa-17032-last-unit", "medusa-17032-counter", "medusa-16502-lines")
RACE = CASES[:2]
CHECKS = (
    "no_oversell",
    "reserved_matches_reservations",
    "one_order_per_cart",
    "no_orphaned_orders",
    "no_missing_orders",
)
BASELINES = Path("benchmark") / "baselines" / "2004ed5"
AGENT = Path("benchmark") / "agent"
CASE_ROOT = Path("benchmark") / "cases"
DOCS = ("README.md", "RESULTS.md", "benchmark/README.md", "benchmark/agent/README.md")
ARMS = ("unguided-none", "unguided-history", "nomenu-none")
NOT_RESULTS = (
    "| Field | Meaning |",
    "| Case | Scoring control | Cross-check | History |",
    "| Version | Tag commit | Files | Bytes |",
    "| Case | Issue | Characters |",
    "| Cause | Meaning | Cases |",
    "| Case | Accepted files |",
    "| Rule | Shape | Issue |",
)


def histories(folder: Path) -> list[dict]:
    out = []
    for p in sorted(Path(folder).glob("run-*.json*")):
        data = p.read_bytes()
        out.append(json.loads(gzip.decompress(data) if p.suffix == ".gz" else data))
    return out


@functools.cache
def fails(folder: Path) -> tuple[dict[str, int], int, int]:
    hs = histories(folder)
    c = score.counts(hs)
    return {k: c.get(k, {}).get("fail", 0) for k in CHECKS}, len(hs), score.inconclusive_runs(hs)


def of(n: int, total: int) -> str:
    return f"{n} of {total}"


def num(value: float) -> str:
    return f"{value:g}"


def median_text(values: list) -> str:
    misses = sum(1 for v in values if v is None)
    if misses * 2 >= len(values):
        return "over 300"
    finite = sorted(v for v in values if v is not None) + [math.inf] * misses
    return num(statistics.median(finite))


def cell(values: list) -> str:
    hits = sum(1 for v in values if v is not None)
    return f"{of(hits, len(values))}, median {median_text(values)}"


def all_three(trials: list[dict]) -> str:
    return of(sum(1 for t in trials if all(t[c] is not None for c in CASES)), len(trials))


class Data:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.cases = score.load_cases(self.root / CASE_ROOT)
        self.rules = {c: self.cases[c].rule for c in self.cases}
        self.full = {c: load_case(self.cases[c].folder) for c in self.cases}
        self._scores: dict[Path, dict] = {}

    def baseline(self, method: str, n: int) -> dict:
        folder = self.root / BASELINES / f"{method}-seed-{n}"
        records = ledger.load(folder / "ledger.jsonl")
        s = score.trial_summary(records, self.rules)
        stamps = [datetime.fromisoformat(r["timestamp"]) for r in records if r.get("timestamp")]
        s["minutes"] = (max(stamps) - min(stamps)).total_seconds() / 60
        s["folder"] = folder
        s["firsts"] = {
            c: s["cases"][c]["runs_to_first"] if s["cases"][c]["reproduced"] else None
            for c in CASES
        }
        return s

    def score(self, folder: Path) -> dict:
        folder = self.root / folder
        if folder not in self._scores:
            self._scores[folder] = json.loads((folder / "score.json").read_text())
        return self._scores[folder]

    def agent_folder(self, arm: str, n: int) -> Path:
        plan = "unguided-haiku-1" if arm.startswith("unguided") and n <= 3 else "scale-10"
        return AGENT / plan / f"{arm}-{n}"

    def agent(self, arm: str, n: int) -> dict:
        s = self.score(self.agent_folder(arm, n))
        return {
            c: s["cases"][c]["runs_to_first"] if s["cases"][c]["reproduced"] else None
            for c in CASES
        }

    def arm(self, arm: str) -> list[dict]:
        if arm in ("grid", "random"):
            return [self.baseline(arm, n)["firsts"] for n in range(1, 11)]
        return [self.agent(arm, n) for n in range(1, 11)]

    def plan_folders(self, plan: str) -> list[Path]:
        base = self.root / AGENT / plan
        return [p.relative_to(self.root) for p in base.iterdir() if (p / "score.json").exists()]


def headline_rows(d: Data, arms: tuple[str, ...]) -> list[list]:
    trials = {a: d.arm(a) for a in arms}
    rows = [[c, *(cell([t[c] for t in trials[a]]) for a in arms)] for c in CASES]
    rows.append([None, *(all_three(trials[a]) for a in arms)])
    return rows


def readme_cases(d: Data) -> list[list]:
    rows = []
    for c in CASES:
        case = d.full[c]
        scoring = case.scoring
        base = d.root / CASE_ROOT / c / "results" / "2004ed5"
        plain, n, _ = fails(base / "2.22.0-reference")
        fixed, m, _ = fails(base / f"2.22.0-{scoring.variant}-control")
        issue = case.issue.url.rsplit("/", 1)[1]
        pr = scoring.variant.split("-", 1)[1]
        rows.append(
            [
                None,
                f"[#{issue}]({case.issue.url})",
                f"{of(plain[case.rule], n)} runs",
                f"{of(fixed[case.rule], m)} runs ([fix #{pr}](https://github.com/medusajs/medusa/pull/{pr}))",
            ]
        )
    return rows


def set_order(name: str) -> tuple:
    if name.endswith("-reference"):
        return (0, name)
    if "-pr-" in name:
        return (1, name)
    return (2, name)


def sets_2004ed5(d: Data) -> list[list]:
    rows = []
    for c in CASES:
        base = d.root / CASE_ROOT / c / "results" / "2004ed5"
        for folder in sorted(
            (p for p in base.iterdir() if p.is_dir()), key=lambda p: set_order(p.name)
        ):
            f, _, inconclusive = fails(folder)
            link = f"[report](cases/{c}/results/2004ed5/{folder.name}/report.md)"
            rows.append([c, None, *(f[k] for k in CHECKS), inconclusive, link])
    return rows


def reproduced_2004ed5(d: Data) -> list[list]:
    rows = []
    for c in CASES:
        case = d.full[c]
        scoring = case.scoring
        base = d.root / CASE_ROOT / c / "results" / "2004ed5"
        plain, n, _ = fails(base / "2.22.0-reference")
        fixed, m, _ = fails(base / f"2.22.0-{scoring.variant}-control")
        word = "reproduced" if plain[case.rule] and not fixed[case.rule] else "not reproduced"
        rows.append(
            [
                c,
                f"{word}: rule failed in {of(plain[case.rule], n)} runs, "
                f"{of(fixed[case.rule], m)} on its scoring control",
            ]
        )
    return rows


def others(f: dict[str, int], rule: str) -> str:
    parts = [f"{k} {f[k]}" for k in CHECKS if k != rule and f[k]]
    return ", ".join(parts) or "none"


def sets_a35d162(d: Data) -> list[list]:
    rows = []
    for c in CASES:
        case = d.full[c]
        base = d.root / CASE_ROOT / c / "results" / "a35d162"
        for version in case.versions:
            for kind, locking in (("reference", "in-memory"), ("redis-control", "redis")):
                folder = base / f"{version}-{kind}"
                if not folder.is_dir():
                    continue
                f, n, inconclusive = fails(folder)
                link = f"[report](cases/{c}/results/a35d162/{folder.name}/report.md)"
                rows.append(
                    [
                        c,
                        version,
                        kind,
                        locking,
                        of(f[case.rule], n),
                        others(f, case.rule),
                        inconclusive,
                        link,
                    ]
                )
    return rows


def reproduced_a35d162(d: Data) -> list[list]:
    rows = []
    for c in CASES:
        case = d.full[c]
        base = d.root / CASE_ROOT / c / "results" / "a35d162"
        row = [c]
        for version in ("2.21.2", "2.19.0", "2.22.0"):
            plain, _, _ = fails(base / f"{version}-reference")
            control = base / f"{version}-redis-control"
            if not plain[case.rule]:
                row.append("not reproduced")
            elif not control.is_dir():
                row.append("reproduced, no control yet")
            else:
                row.append("reproduced" if not fails(control)[0][case.rule] else "not reproduced")
        rows.append(row)
    return rows


def sets_earlier(d: Data) -> list[list]:
    rows = []
    for c in CASES:
        case = d.full[c]
        results = d.root / CASE_ROOT / c / "results"
        for version in case.versions:
            for pin in sorted(
                p.name for p in results.iterdir() if p.name not in ("2004ed5", "a35d162")
            ):
                for kind, label in (("reference", "reference"), ("control", "one-server control")):
                    folder = results / pin / f"{version}-{kind}"
                    if not folder.is_dir():
                        continue
                    f, n, inconclusive = fails(folder)
                    link = f"[report](cases/{c}/results/{pin}/{folder.name}/report.md)"
                    rows.append(
                        [
                            c,
                            version,
                            f"`{pin}`",
                            label,
                            of(f[case.rule], n),
                            others(f, case.rule),
                            inconclusive,
                            link,
                        ]
                    )
    return rows


def fixed_guesses(d: Data) -> list[list]:
    folders = [d.cases[c].folder for c in CASES]
    module = "packages/modules/inventory/src/services/inventory-module.ts"
    rows = []
    for file, cause in (
        (module, None),
        (None, "process-local-lock"),
        (module, "process-local-lock"),
    ):
        g = answers.fixed_guess(folders, file, cause)
        rows.append([None, *(of(g[p], g["cases"]) for p in answers.PARTS)])
    return rows


def baseline_rows(d: Data) -> list[list]:
    rows = []
    for method, label in (("grid", "grid order seed"), ("random", "random seed")):
        for n in range(1, 11):
            s = d.baseline(method, n)
            firsts = [
                str(s["firsts"][c]) if s["firsts"][c] is not None else "not reproduced"
                for c in CASES
            ]
            rows.append(
                [
                    f"[{label} {n}](baselines/2004ed5/{method}-seed-{n}/)",
                    of(s["reached"], s["candidates"]),
                    s["runs_used"],
                    of(s["cases_reproduced"], 3),
                    *firsts,
                    s["violations"],
                    s["cause_not_isolated"],
                    s["cut_off_by_run_cap"],
                ]
            )
    return rows


def review_cells(folder: Path, sets: dict, keys: tuple[str, ...], rule: str) -> list[str]:
    out = []
    for k in keys:
        f, n, _ = fails(folder / sets[k]["folder"])
        out.append(of(f[rule], n))
    return out


def seed_reviews(d: Data) -> list[list]:
    rows = []
    keys = ("plain", "pr-16961-redis", "pr-16961", "redis")
    for n in range(1, 11):
        folder = d.root / BASELINES / f"random-seed-{n}" / "review"
        if not (folder / "review.json").exists():
            continue
        sets = json.loads((folder / "review.json").read_text())["attempts"][0]["sets"]
        rows.append(
            [f"random seed {n}", "`no_oversell`", *review_cells(folder, sets, keys, "no_oversell")]
        )
    return rows


def ablation(d: Data) -> list[list]:
    v2 = d.arm("unguided-none")
    nomenu = d.arm("nomenu-none")
    rows = []
    for c in RACE:
        options = set()
        for i, t in enumerate(nomenu):
            if all(t[x] is not None for x in RACE):
                values = [None if j == i else u[c] for j, u in enumerate(nomenu)]
                options.add(cell(values))
        missed = options.pop() if len(options) == 1 else "ambiguous"
        rows.append([c, cell([t[c] for t in v2]), cell([t[c] for t in nomenu]), missed])
    return rows


def reproduced_text(s: dict) -> str:
    hits = [
        f"{c} (run {s['cases'][c]['runs_to_first']})"
        for c in sorted(CASES)
        if s["cases"][c]["reproduced"]
    ]
    return ", ".join(hits) or "none"


def trial_cells(s: dict) -> list:
    claims = (
        "no finish" if s["claims"] is None else f"{s['claims_backed']} / {s['claims_unbacked']}"
    )
    exp = s["expected_check"]
    return [
        s["turns"],
        f"{s['attempts']} ({s['refused']})",
        s["oversold_runs"],
        reproduced_text(s),
        claims,
        of(exp["hits"], exp["of"]),
        f"{s['dollars']:.4f}",
    ]


def issue_ref(d: Data, s: dict) -> str:
    return "#" + d.full[s["issue"]].issue.url.rsplit("/", 1)[1]


def plan_rows(d: Data, plan: str, order: list[str], extra) -> list[list]:
    rows = []
    for name in order:
        s = d.score(AGENT / plan / name)
        rows.append([f"[{name}]({plan}/{name}/)", *extra(name, s), *trial_cells(s)])
    return rows


def scale_rows(d: Data) -> list[list]:
    order = [
        f"{a}-{n}"
        for a in ARMS
        for n in range(1, 11)
        if (d.root / AGENT / "scale-10" / f"{a}-{n}").is_dir()
    ]
    return plan_rows(
        d,
        "scale-10",
        order,
        lambda name, s: ["v2-nomenu" if name.startswith("nomenu") else "v2", s["feedback"]],
    )


def unguided_rows(d: Data) -> list[list]:
    order = [f"unguided-{f}-{n}" for f in ("none", "history") for n in (1, 2, 3)]
    return plan_rows(d, "unguided-haiku-1", order, lambda name, s: [s["feedback"]])


def guided2_rows(d: Data) -> list[list]:
    order = [f"17032-{f}-{n}" for f in ("none", "history") for n in (1, 2, 3)]
    return plan_rows(d, "guided-haiku-2", order, lambda name, s: [s["feedback"]])


def guided1_rows(d: Data) -> list[list]:
    order = [f"{i}-{f}-{n}" for i in (16502, 17032) for f in ("none", "history") for n in (1, 2, 3)]
    return plan_rows(d, "guided-haiku-1", order, lambda name, s: [issue_ref(d, s), s["feedback"]])


def unguided_reviews(d: Data) -> list[list]:
    rows = []
    for name in ("unguided-history-2", "unguided-history-3"):
        folder = d.root / AGENT / "unguided-haiku-1" / name / "review"
        review = json.loads((folder / "review.json").read_text())
        rule = review["check"]
        cells = review_cells(folder, review["sets"], ("plain", "pr-17420", "redis"), rule)
        rows.append([name, None, f"{rule}", *cells])
    return rows


def guided_compare(d: Data) -> list[list]:
    rows = []
    for c in CASES:
        row = [c]
        for feedback in ("none", "history"):
            for plan in ("guided-haiku-1", "guided-haiku-2"):
                hits = sum(
                    d.score(AGENT / plan / f"17032-{feedback}-{n}")["cases"][c]["reproduced"]
                    for n in (1, 2, 3)
                )
                row.append(of(hits, 3))
        rows.append(row)
    return rows


def results_headline(d: Data) -> list[list]:
    return headline_rows(d, ("grid", "random", "unguided-none", "unguided-history", "nomenu-none"))


def results_costs(d: Data) -> list[list]:
    rows = []
    for method in ("grid", "random"):
        ss = [d.baseline(method, n) for n in range(1, 11)]
        rows.append(
            [
                None,
                len(ss),
                num(statistics.median(s["runs_used"] for s in ss)),
                num(round(statistics.median(s["minutes"] for s in ss))),
                "0",
                "0",
            ]
        )
    for arm in ARMS:
        ss = [d.score(d.agent_folder(arm, n)) for n in range(1, 11)]
        rows.append(
            [
                None,
                len(ss),
                num(statistics.median(s["oversold_runs"] for s in ss)),
                num(round(statistics.median(s["wall_seconds"] for s in ss) / 60, 1)),
                f"{statistics.median(s['dollars'] for s in ss):.4f}",
                f"{sum(s['dollars'] for s in ss):.4f}",
            ]
        )
    return rows


def results_claims(d: Data) -> list[list]:
    rows = []
    for arm in ARMS:
        ss = [d.score(d.agent_folder(arm, n)) for n in range(1, 11)]
        rows.append(
            [
                None,
                len(ss),
                sum(1 for s in ss if s["claims"] is not None),
                sum(s["claims_backed"] for s in ss),
                sum(s["claims_unbacked"] for s in ss),
            ]
        )
    return rows


def results_located(d: Data) -> list[list]:
    rows = []
    for arm in ARMS:
        ss = [d.score(d.agent_folder(arm, n)) for n in range(1, 11)]
        for c in CASES:
            hits = [s["cases"][c] for s in ss if s["cases"][c]["reproduced"]]
            if not hits:
                continue
            files = sum(1 for h in hits if h["file_grade"] == answers.ACCEPTED)
            if arm.startswith("nomenu"):
                causes = "not asked"
            else:
                causes = of(sum(1 for h in hits if h["cause_grade"] == answers.ACCEPTED), len(hits))
            rows.append([None, c, len(hits), of(files, len(hits)), causes])
    return rows


def results_guided(d: Data) -> list[list]:
    rows = []
    cells = (
        ("guided-haiku-1", 16502, "none"),
        ("guided-haiku-1", 16502, "history"),
        ("guided-haiku-1", 17032, "none"),
        ("guided-haiku-1", 17032, "history"),
        ("guided-haiku-2", 17032, "none"),
        ("guided-haiku-2", 17032, "history"),
    )
    for plan, issue, feedback in cells:
        ss = [d.score(AGENT / plan / f"{issue}-{feedback}-{n}") for n in (1, 2, 3)]
        own = [c for c in CASES if str(issue) in c]
        hits = sum(1 for s in ss if any(s["cases"][c]["reproduced"] for c in own))
        rows.append(
            [
                f"#{issue}",
                "v1" if plan == "guided-haiku-1" else "v2",
                feedback,
                len(ss),
                of(hits, len(ss)),
            ]
        )
    return rows


STAT_ARMS = (
    ("unguided-none", "No feedback"),
    ("unguided-history", "With feedback"),
    ("nomenu-none", "No cause list"),
)
STAT_BASES = (("grid", "Grid"), ("random", "Random"))
MISS = 301


def found(trials: list[dict], case: str | None) -> int:
    if case is None:
        return sum(1 for t in trials if all(t[c] is not None for c in CASES))
    return sum(1 for t in trials if t[case] is not None)


def p_text(p: float) -> str:
    return "under 0.0001" if p < 0.0001 else f"{p:.2g}"


def holm_text(p: float) -> str:
    return f"{p_text(p)}, passes" if p < 0.05 else p_text(p)


def fisher_tests(d: Data) -> list[dict]:
    tests = []
    for arm, label in STAT_ARMS:
        agent = d.arm(arm)
        for base, base_label in STAT_BASES:
            other = d.arm(base)
            for case in (*CASES, None):
                a, b = found(agent, case), found(other, case)
                tests.append(
                    {
                        "arm": arm,
                        "row": [label, base_label, case or "All three in one trial"],
                        "a": of(a, len(agent)),
                        "b": of(b, len(other)),
                        "p": stats.fisher_exact(a, len(agent) - a, b, len(other) - b),
                    }
                )
    for t, h in zip(tests, stats.holm([t["p"] for t in tests]), strict=True):
        t["holm_all"] = h
    own = [t for t in tests if t["arm"] == "unguided-none"]
    for t, h in zip(own, stats.holm([t["p"] for t in own]), strict=True):
        t["holm_own"] = h
    return tests


def results_fisher(d: Data) -> list[list]:
    return [
        [
            *t["row"],
            t["a"],
            t["b"],
            p_text(t["p"]),
            holm_text(t["holm_all"]),
            holm_text(t["holm_own"]) if "holm_own" in t else "not in this group",
        ]
        for t in fisher_tests(d)
    ]


def results_versions(d: Data) -> list[list]:
    base = d.arm("unguided-none")
    rows = []
    for arm, label in STAT_ARMS[1:]:
        other = d.arm(arm)
        for case in (*CASES, None):
            a, b = found(base, case), found(other, case)
            p = stats.fisher_exact(a, len(base) - a, b, len(other) - b)
            rows.append(
                [
                    label,
                    case or "All three in one trial",
                    of(a, len(base)),
                    of(b, len(other)),
                    p_text(p),
                ]
            )
    return rows


def results_speed(d: Data) -> list[list]:
    agent = d.arm("unguided-none")
    rows = []
    for base, label in STAT_BASES:
        other = d.arm(base)
        for c in RACE:
            x = [t[c] if t[c] is not None else MISS for t in agent]
            y = [t[c] if t[c] is not None else MISS for t in other]
            rows.append(
                [
                    c,
                    label,
                    median_text([t[c] for t in agent]),
                    median_text([t[c] for t in other]),
                    p_text(stats.mann_whitney(x, y)),
                ]
            )
    return rows


STOPPED = AGENT / "stopped"
STOPPED_RECORDS = (
    ("scale-10-nomenu-none-8", "nomenu-none-8, 10-trial plan"),
    ("followups-1-sonnet-none-3", "sonnet-none-3, follow-up plan"),
)
STOPPED_SETS = {
    "as-is": "Run again as is",
    "as-is-600": "Run again as is",
    "redis": "Redis locking",
    "one-server": "Both completions on one server",
    "server-1": "All completions sent to server 1",
    "stock-5": "Stock raised from 1 to 5",
    "pr-17420": "With the #17032 fix, pull request #17420",
}


def stopped_rows(d: Data) -> list[list]:
    rows = []
    for folder, label in STOPPED_RECORDS:
        base = d.root / STOPPED / folder
        review = json.loads((base / "review" / "review.json").read_text(encoding="utf-8"))
        records = [json.loads(x) for x in (base / "ledger.jsonl").read_text().splitlines()]
        final = next(
            r
            for r in records
            if r.get("kind") == "final" and r.get("attempt_id") == review["attempt_id"]
        )
        runs = fails = 0
        for name, counts in final["candidate_fails"].items():
            if counts is None:
                continue
            runs += final.get(f"{name}_runs") or 0
            fails += counts["one_order_per_cart"]
        rows.append([label, "The trial's own runs", runs, fails])
        for name, data in review["sets"].items():
            rows.append(
                [label, STOPPED_SETS[name], data["runs"], data["fails"]["one_order_per_cart"]]
            )
    return rows


CHECKED = {
    "README.md": {
        "| Test scenario | Public bug | Rule broken on plain Medusa |": readme_cases,
    },
    "RESULTS.md": {
        "| Test scenario | Grid | Random | Agent, no feedback |": results_headline,
        "| Method | Trials | Median runs used |": results_costs,
        "| Method | Trials | Trials that called finish |": results_claims,
        "| Method | Test scenario | Trials that reproduced it |": results_located,
        "| Bug report given | Prompt | Feedback |": results_guided,
        "| Agent version | Compared with | Scenario |": results_fisher,
        "| Scenario | Compared with | Agent median runs |": results_speed,
        "| No-feedback agent against | Scenario |": results_versions,
        "| Stopped trial | Test | Runs |": stopped_rows,
    },
    "benchmark/README.md": {
        "| Case | Set | no_oversell 2 |": sets_2004ed5,
        "| Case | 2.22.0 at v0.1.1 |": reproduced_2004ed5,
        "| Case | Version | Set | Locking |": sets_a35d162,
        "| Case | 2.21.2 | 2.19.0 | 2.22.0 |": reproduced_a35d162,
        "| Case | Version | Oversold | Set |": sets_earlier,
        "| Fixed guess | File accepted | Cause accepted | Located |": fixed_guesses,
        "| Trial | Candidates reached | Runs used |": baseline_rows,
        "| Trial | Check | Plain Medusa | pr-16961 with Redis locking |": seed_reviews,
    },
    "benchmark/agent/README.md": {
        "| Test scenario | Grid (no AI) | Random (no AI) |": lambda d: headline_rows(
            d, ("grid", "random", "unguided-none", "unguided-history")
        ),
        "| Test scenario | v2, feedback none | v2-nomenu, with the rerun |": ablation,
        "| Trial | Prompts | Feedback |": scale_rows,
        "| Trial | Feedback | Turns |": None,
        "| Trial | Scenario | Check |": unguided_reviews,
        "| Test scenario | v1, none | v2, none | v1, history | v2, history |": guided_compare,
        "| Trial | Bug report | Feedback |": guided1_rows,
    },
}

SAME_HEADER = {"| Trial | Feedback | Turns |": (unguided_rows, guided2_rows)}


def split(line: str) -> list[str]:
    return [c.strip() for c in line.strip()[1:-1].split(" | ")]


def doc_tables(text: str) -> list[tuple[str, list[list[str]]]]:
    out: list[tuple[str, list[list[str]]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            out.append((block[0], [split(x) for x in block[2:]]))
        else:
            i += 1
    return out


def compare(where: str, rows: list[list[str]], expected: list[list]) -> list[str]:
    problems = []
    if len(rows) != len(expected):
        return [f"{where}: {len(rows)} rows, the data gives {len(expected)}"]
    for r, (got, want) in enumerate(zip(rows, expected, strict=True), start=1):
        if len(got) != len(want):
            problems.append(f"{where} row {r}: {len(got)} cells, expected {len(want)}")
            continue
        for k, (g, w) in enumerate(zip(got, want, strict=True), start=1):
            if w is not None and g != str(w):
                problems.append(
                    f"{where} row {r} cell {k}: the doc says {g!r}, the data gives {str(w)!r}"
                )
    return problems


def problems(root: Path, texts: dict[str, str] | None = None, d: Data | None = None) -> list[str]:
    root = Path(root)
    d = d or Data(root)
    texts = texts or {}
    out = []
    for doc in DOCS:
        path = root / doc
        if doc not in texts and not path.exists():
            out.append(f"{doc} is missing")
            continue
        text = texts[doc] if doc in texts else path.read_text(encoding="utf-8")
        checked = CHECKED.get(doc, {})
        repeats: dict[str, int] = {}
        found: set[str] = set()
        for header, rows in doc_tables(text):
            key = next((k for k in checked if header.startswith(k)), None)
            if key is None:
                if not any(header.startswith(k) for k in NOT_RESULTS):
                    out.append(f"{doc}: the table {header[:60]!r} is not checked")
                continue
            found.add(key)
            if key in SAME_HEADER:
                n = repeats.get(key, 0)
                repeats[key] = n + 1
                makers = SAME_HEADER[key]
                if n >= len(makers):
                    out.append(f"{doc}: one more {key!r} table than expected")
                    continue
                maker = makers[n]
            else:
                maker = checked[key]
            out += compare(f"{doc} {key[:40]!r}", rows, maker(d))
        for key in checked:
            if key not in found:
                out.append(f"{doc}: no table starting {key[:60]!r}")
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    found = problems(root)
    for line in found:
        print(line)
    print(f"{len(found)} problems")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
