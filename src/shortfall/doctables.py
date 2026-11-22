import functools
import gzip
import json
import math
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

import yaml

from shortfall import agent, answers, ledger, score, stats
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
DOCS = (
    "README.md",
    "RESULTS.md",
    "benchmark/README.md",
    "benchmark/agent/README.md",
    "WALKTHROUGH.md",
)
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
        self._unknown: dict[str, int] | None = None

    def unknown_runs(self) -> dict[str, int]:
        if self._unknown is None:
            out = dict.fromkeys(("runs", "unknown", "inconclusive", "oversold_pass"), 0)
            folders = sorted({p.parent for p in (self.root / "benchmark").rglob("run-*.json*")})
            for folder in folders:
                for h in histories(folder):
                    out["runs"] += 1
                    if not score.unknown_completion(h):
                        continue
                    out["unknown"] += 1
                    c = score.counts([h])
                    out["inconclusive"] += (
                        all(
                            row["inconclusive"] == 1 and row["pass"] == 0 and row["fail"] == 0
                            for row in c.values()
                        )
                        and score.inconclusive_runs([h]) == 1
                    )
                    out["oversold_pass"] += bool(h.get("verdicts")) and all(
                        v["result"] == "pass" for v in h["verdicts"]
                    )
            self._unknown = out
        return self._unknown

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
                causes = named = "not asked"
            else:
                causes = of(sum(1 for h in hits if h["cause_grade"] == answers.ACCEPTED), len(hits))
                both = sum(
                    1
                    for h in hits
                    if h["file_grade"] == answers.ACCEPTED and h["cause_grade"] == answers.ACCEPTED
                )
                named = of(both, len(hits))
            rows.append([None, c, len(hits), of(files, len(hits)), causes, named])
    return rows


def results_fixed(d: Data) -> list[list]:
    folders = [d.cases[c].folder for c in CASES]
    file, _ = answers.most_common(folders, "files")
    cause, _ = answers.most_common(folders, "causes")
    rows = []
    for label, guess in (
        (f"Always `{Path(file).name}`, no cause", (file, None)),
        (f"Always the most common cause, `{cause}`, no file", (None, cause)),
        (f"Always `{Path(file).name}` and `{cause}`", (file, cause)),
    ):
        g = answers.fixed_guess(folders, *guess)
        rows.append(
            [
                label,
                of(g["file"], g["cases"]),
                of(g["cause"], g["cases"]),
                of(g["located"], g["cases"]),
            ]
        )
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


FOLLOWUPS = AGENT / "followups-1"
FOLLOW_TESTED = (("budget2-none", "Haiku 5.5, whole budget"), ("sonnet-none", "Sonnet 5.5"))
FOLLOW_ARMS = (*FOLLOW_TESTED, ("budget-none", "Haiku 5.5, first gate, closed"))
FOLLOW_ORDER = (("budget-none", 3), ("budget2-none", 10), ("sonnet-none", 10))
FOLLOW_PROMPTS = {"budget-none": "v2-budget", "budget2-none": "v2-budget2", "sonnet-none": "v2"}
FOLLOW_HELD = ("sonnet-none-3", "sonnet-none-5", "budget2-none-6")


def follow_folders(d: Data, arm: str) -> list[Path]:
    return [
        FOLLOWUPS / f"{arm}-{n}"
        for n in range(1, 11)
        if (d.root / FOLLOWUPS / f"{arm}-{n}" / "score.json").exists()
    ]


def follow_arm(d: Data, arm: str) -> list[dict]:
    out = []
    for folder in follow_folders(d, arm):
        s = d.score(folder)
        out.append(
            {
                c: s["cases"][c]["runs_to_first"] if s["cases"][c]["reproduced"] else None
                for c in CASES
            }
        )
    return out


def follow_tests(d: Data) -> list[dict]:
    haiku, grid = d.arm("unguided-none"), d.arm("grid")
    tests = []
    for arm, label in FOLLOW_TESTED:
        trials = follow_arm(d, arm)
        own = []
        for case, other, other_label, kind in (
            (None, haiku, "Haiku 5.5 on v2", "primary"),
            *((c, haiku, "Haiku 5.5 on v2", "secondary") for c in CASES),
            *((c, grid, "Grid", "secondary") for c in (*CASES, None)),
        ):
            a, b = found(trials, case), found(other, case)
            own.append(
                {
                    "row": [label, kind, other_label, case or "All three in one trial"],
                    "a": of(a, len(trials)),
                    "b": of(b, len(other)),
                    "p": stats.fisher_exact(a, len(trials) - a, b, len(other) - b),
                }
            )
        for t, h in zip(own, stats.holm([t["p"] for t in own]), strict=True):
            t["holm"] = h
        tests += own
    return tests


def follow_test_rows(d: Data) -> list[list]:
    return [
        [*t["row"], t["a"], t["b"], p_text(t["p"]), holm_text(t["holm"])] for t in follow_tests(d)
    ]


def follow_headline(d: Data) -> list[list]:
    arms = [
        d.arm("unguided-none"),
        *(follow_arm(d, a) for a, _ in FOLLOW_TESTED),
        d.arm("grid"),
        follow_arm(d, "budget-none"),
    ]
    rows = [[c, *(cell([t[c] for t in trials]) for trials in arms)] for c in CASES]
    rows.append([None, *(all_three(trials) for trials in arms)])
    return rows


def readme_follow(d: Data) -> list[list]:
    arms = [d.arm("unguided-none"), *(follow_arm(d, a) for a, _ in FOLLOW_TESTED), d.arm("grid")]
    rows = [[c, *(of(found(trials, c), len(trials)) for trials in arms)] for c in CASES]
    rows.append([None, *(all_three(trials) for trials in arms)])
    return rows


def follow_costs(d: Data) -> list[list]:
    rows = []
    for arm, label in FOLLOW_ARMS:
        ss = [d.score(f) for f in follow_folders(d, arm)]
        gates = [s.get("gate_answers") or 0 for s in ss]
        rows.append(
            [
                label,
                len(ss),
                num(statistics.median(s["oversold_runs"] for s in ss)),
                num(statistics.median(s["turns"] for s in ss)),
                num(statistics.median(s["attempts"] for s in ss)),
                sum(1 for s in ss if s["finished_by_model"]),
                sum(s["claims_backed"] for s in ss),
                sum(s["claims_unbacked"] for s in ss),
                f"{statistics.median(s['dollars'] for s in ss):.4f}",
                f"{sum(s['dollars'] for s in ss):.4f}",
                num(round(statistics.median(s["wall_seconds"] for s in ss) / 60, 1)),
                num(statistics.median(gates)) if arm.startswith("budget") else "none",
            ]
        )
    return rows


def follow_rows(d: Data) -> list[list]:
    order = [
        f"{arm}-{n}"
        for arm, count in FOLLOW_ORDER
        for n in range(1, count + 1)
        if (d.root / FOLLOWUPS / f"{arm}-{n}" / "score.json").exists()
    ]

    def extra(name: str, s: dict) -> list:
        arm = name.rsplit("-", 1)[0]
        gates = s.get("gate_answers")
        return [
            s["model"],
            FOLLOW_PROMPTS[arm],
            s["end_reason"],
            "not gated" if gates is None else gates,
        ]

    return plan_rows(d, "followups-1", order, extra)


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
        runs, n = held_own_runs(final, "one_order_per_cart")
        rows.append([label, "The trial's own runs", runs, n])
        for name, data in review["sets"].items():
            rows.append(
                [label, STOPPED_SETS[name], data["runs"], data["fails"]["one_order_per_cart"]]
            )
    return rows


def held_own_runs(final: dict, rule: str) -> tuple[int, int]:
    runs = fails = 0
    for name, counts in final["candidate_fails"].items():
        if counts is None:
            continue
        runs += final.get(f"{name}_runs") or 0
        fails += counts[rule]
    return runs, fails


def follow_hand_rows(d: Data) -> list[list]:
    rows = []
    for trial in FOLLOW_HELD:
        base = d.root / FOLLOWUPS / trial
        review = json.loads((base / "review" / "review.json").read_text(encoding="utf-8"))
        records = ledger.load(base / "ledger.jsonl")
        for item in review["attempts"]:
            final = next(
                r
                for r in records
                if r.get("kind") == "final" and r.get("attempt_id") == item["attempt_id"]
            )
            label = f"{trial}, attempt {int(item['attempt_id'].rsplit('-', 1)[1])}"
            runs, n = held_own_runs(final, "one_order_per_cart")
            rows.append([label, "The trial's own runs", runs, n])
            for name, data in item["sets"].items():
                counts, total, _ = fails(base / "review" / data["folder"])
                rows.append([label, STOPPED_SETS[name], total, counts["one_order_per_cart"]])
    return rows


CASE_FIX = {
    "medusa-17032-last-unit": "pr-17420",
    "medusa-17032-counter": "pr-17420",
    "medusa-16502-lines": "pr-16961",
}
REVIEW_COVER = {
    "covered by #17032, rare in this scenario": ("pr-17420", "redis"),
    "covered by #16502 and #17032 together": ("pr-16961-redis",),
    "documented limit of in-memory locking": ("redis",),
}


def published_ledgers(d: Data) -> list[Path]:
    roots = [d.root / AGENT, d.root / BASELINES]
    return sorted({p.parent for r in roots for p in r.rglob("ledger.jsonl")})


def reference_controls(d: Data) -> tuple[list[int], list[int]]:
    fix, redis = [0, 0], [0, 0]
    for c in CASES:
        rule = d.rules[c]
        for folder in sorted((d.root / CASE_ROOT / c / "results").glob("*/*")):
            hs = histories(folder)
            if not hs:
                continue
            target = hs[0].get("target") or {}
            variant = (target.get("variant") or {}).get("name")
            f, n, _ = fails(folder)
            if variant == CASE_FIX[c]:
                fix[0] += n
                fix[1] += f[rule]
            elif target.get("locking") == "redis" and CASE_FIX[c] == "pr-17420":
                redis[0] += n
                redis[1] += f[rule]
    return fix, redis


def scoring_controls(d: Data) -> tuple[list[int], list[int]]:
    credited, other = [0, 0], [0, 0]
    for folder in published_ledgers(d):
        for r in ledger.load(folder / "ledger.jsonl"):
            if r.get("kind") != "final":
                continue
            cases = (r.get("reproduced") or {}).get("cases") or {}
            for control in r.get("controls") or []:
                names = control.get("cases") or []
                fl = control.get("fails") or {}
                won = [c for c in names if cases.get(c) == score.REPRODUCED]
                bucket = credited if won else other
                bucket[0] += control.get("runs") or 0
                bucket[1] += max((fl.get(d.rules[c], 0) for c in won or names), default=0)
    return credited, other


def review_files(d: Data) -> list[Path]:
    roots = [d.root / AGENT, d.root / BASELINES]
    return sorted(p for r in roots for p in r.rglob("review/review.json"))


def review_items(path: Path) -> list[tuple[str, list[str], dict]]:
    review = json.loads(path.read_text(encoding="utf-8"))
    if review.get("attempts"):
        return [(a["label"], a["rules"], a["sets"]) for a in review["attempts"]]
    rule = review.get("check") or HAND_RULE
    return [(review["label"], [rule], review["sets"])]


def review_controls(d: Data) -> list[int]:
    out = [0, 0]
    for path in review_files(d):
        for label, rules, sets in review_items(path):
            for name in REVIEW_COVER[label]:
                if name not in sets:
                    continue
                f, n, _ = fails(path.parent / sets[name]["folder"])
                out[0] += n
                out[1] += max(f.get(rule, 0) for rule in rules)
    return out


def negative_rows(d: Data) -> list[list]:
    fix, redis = reference_controls(d)
    credited, other = scoring_controls(d)
    reviewed = review_controls(d)
    covered = [fix, redis, credited, reviewed]
    rows = [
        ["The three reference scenarios on their fix build", *fix],
        ["The two #17032 reference scenarios with Redis locking", *redis],
        ["Fix-build controls of tests credited as reproduced", *credited],
        ["Review runs with the fix or locking the review found covers the failure", *reviewed],
        ["All of the above", sum(x[0] for x in covered), sum(x[1] for x in covered)],
        ["For contrast: fix-build controls of tests not credited to that fix", *other],
    ]
    return rows


HAND_RULE = "one_order_per_cart"


def pooled_rows(d: Data) -> list[list]:
    rows = []
    for label, names in (
        ("Two servers, in-memory lock, run again as is", ("as-is", "as-is-600")),
        ("Redis locking", ("redis",)),
        ("Every checkout on one server", ("one-server", "server-1")),
    ):
        runs = failed = 0
        for path in review_files(d):
            for item_label, _rules, sets in review_items(path):
                if item_label != "documented limit of in-memory locking":
                    continue
                for name in names:
                    if name in sets:
                        f, n, _ = fails(path.parent / sets[name]["folder"])
                        runs += n
                        failed += f[HAND_RULE]
        bound = f"{1 - 0.05 ** (1 / runs):.2%}" if runs and not failed else "does not apply"
        rows.append([label, runs, failed, bound])
    return rows


WALK = AGENT / "scale-10" / "unguided-none-5"
WALK_MISS = AGENT / "scale-10" / "unguided-none-4"
WALK_BIG = AGENT / "followups-1" / "sonnet-none-6"
WALK_RUN = "20261118T060640Z-attempt-01-agent-20261118t060622z-2.22.0"
WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")
BUILDS = {
    None: "Plain Medusa 2.22.0",
    "pr-16961": "With the #16502 fix, pr-16961",
    "pr-17420": "With the #17032 fix, pr-17420",
}


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def transcript(d: Data, folder: Path) -> list[dict]:
    body = gzip.decompress((d.root / folder / "transcript.jsonl.gz").read_bytes())
    return [json.loads(x) for x in body.decode("utf-8").splitlines()]


def records(d: Data, folder: Path) -> list[dict]:
    return ledger.load(d.root / folder / "ledger.jsonl")


def walk_steps(d: Data) -> list[list]:
    events = transcript(d, WALK)
    results = {e["call"]: e["content"] for e in events if e.get("event") == "tool"}
    rows: list[list] = []
    sent = 0
    for e in events:
        if e.get("event") != "reply":
            continue
        for call in e["message"].get("tool_calls") or []:
            a = call["arguments"]
            if call["name"] == "search":
                what = f"Searched `{a.get('path', '.')}` for `{a['text']}`"
            elif call["name"] == "read_file":
                head = results[call["id"]].splitlines()[0]
                m = re.match(r"(.+), lines (\d+) to (\d+) of \d+$", head)
                what = f"Read `{m.group(1)}`, lines {m.group(2)} to {m.group(3)}"
            elif call["name"] == "list_files":
                what = f"Listed `{a['path']}`"
            elif call["name"] == "submit_attempt":
                sent += 1
                what = f"Sent attempt {sent}"
            elif call["name"] == "finish":
                n = len(a.get("claims") or [])
                what = (
                    "Called finish with no claims" if n == 0 else f"Called finish with {n} claims"
                )
            else:
                what = call["name"]
            rows.append([len(rows) + 1, what, None])
    return rows


def walk_prediction(d: Data) -> list[list]:
    first = min(
        (r for r in records(d, WALK) if r.get("kind") == "prediction"), key=lambda r: r["attempt"]
    )
    s = d.score(WALK)
    named = [
        c
        for c in CASES
        if s["cases"][c]["reproduced"]
        and s["cases"][c]["attempt"] == first["attempt"]
        and s["cases"][c]["file_grade"] == answers.ACCEPTED
        and s["cases"][c]["cause_grade"] == answers.ACCEPTED
    ]
    return [
        ["File", f"`{first['file']}`"],
        ["Cause", f"`{first['cause']}`"],
        ["Check it expected to fail", f"`{first['expected_check']}`"],
        ["Named the right place", "yes, for " + " and ".join(named) if named else "no"],
    ]


def walk_folders(d: Data, attempt: int) -> dict[str | None, list[Path]]:
    final = next(
        r
        for r in records(d, WALK)
        if r.get("kind") == "final" and r["attempt_id"].endswith(f"-{attempt:02d}")
    )
    out: dict[str | None, list[Path]] = {}
    for name in final["run_folders"]:
        m = re.search(r"-(pr-\d+)-control-", name)
        out.setdefault(m.group(1) if m else None, []).append(
            d.root / WALK / "runs" / Path(name).name
        )
    return out


def walk_results(d: Data) -> list[list]:
    rows = []
    for variant, folders in walk_folders(d, 1).items():
        total = dict.fromkeys(CHECKS, 0)
        runs = 0
        for folder in folders:
            f, n, _ = fails(folder)
            runs += n
            for k in CHECKS:
                total[k] += f[k]
        rows.append([BUILDS[variant], runs, *(total[k] for k in CHECKS)])
    return rows


def walk_end(d: Data) -> list[list]:
    s = d.score(WALK)
    claims = s["claims"] or []
    return [
        ["Attempts", s["attempts"]],
        ["Claims", len(claims)],
        ["Claims backed by a violation", s["claims_backed"]],
        ["Runs used", f"{s['oversold_runs']} of {s['caps']['runs']}"],
        ["Turns", f"{s['turns']} of {s['caps']['turns']}"],
        ["Cost", f"${s['dollars']:.4f}"],
        ["Time", f"{num(round(s['wall_seconds'] / 60, 1))} minutes"],
    ]


def rules_text(v: dict) -> str:
    rules = [r for r in CHECKS if v["rules"].get(r)]
    counts = {v["rules"][r] for r in rules}
    names = " and ".join(f"`{r}`" for r in rules)
    if len(counts) == 1:
        return f"{names} in {counts.pop()} of {v['runs']} runs"
    return ", ".join(f"`{r}` in {v['rules'][r]}" for r in rules) + f" of {v['runs']} runs"


def walk_big(d: Data) -> list[list]:
    rows = []
    for r in records(d, WALK_BIG):
        if r.get("kind") != "final":
            continue
        cases = (r.get("reproduced") or {}).get("cases") or {}
        hits = [c for c in CASES if cases.get(c) == score.REPRODUCED]
        at = r.get("reproduced_at") or {}
        rows.append(
            [
                int(r["attempt_id"].rsplit("-", 1)[1]),
                None,
                rules_text(r["violation"]),
                ", ".join(f"{c} (run {at[c]})" for c in hits) or "none",
            ]
        )
    return rows


def walk_scenario(d: Data) -> str:
    return (d.root / WALK / "attempts" / "attempt-01.yaml").read_text(encoding="utf-8").rstrip()


def walk_excerpt(d: Data) -> str:
    folder = d.root / WALK / "runs" / WALK_RUN
    h = next(
        h
        for h in histories(folder)
        if any(v["check"] == "no_oversell" and v["result"] == "fail" for v in h["verdicts"])
    )
    keep = ("id", "step", "cart", "server", "status", "outcome")
    race = [{k: op[k] for k in keep} for op in h["operations"] if op.get("phase") == "race"]
    verdicts = [
        {k: v[k] for k in ("check", "result", "reason")}
        for v in h["verdicts"]
        if v["result"] == "fail"
    ]
    lines = ["{", ' "race": [']
    lines += [f"  {json.dumps(op)}," for op in race]
    lines[-1] = lines[-1].rstrip(",")
    lines += [" ],", ' "failed checks": [']
    lines += [f"  {json.dumps(v)}," for v in verdicts]
    lines[-1] = lines[-1].rstrip(",")
    lines += [" ]", "}"]
    return "\n".join(lines)


def walk_prose_found(d: Data) -> list[str]:
    trials = d.arm("unguided-none")
    races = sum(1 for t in trials if all(t[c] is not None for c in RACE))
    return [str(races), str(len(trials)), str(found(trials, None)), str(len(trials))]


def walk_prose_run(d: Data) -> list[str]:
    s = d.score(WALK)
    runs = {s["cases"][c]["runs_to_first"] for c in RACE}
    return [str(runs.pop()) if len(runs) == 1 else "differs"]


def walk_prose_scenario(d: Data) -> list[str]:
    data = yaml.safe_load(walk_scenario(d))
    return [word(data["target"]["servers"]), str(data["stock"]["SOLO"])]


def walk_prose_miss(d: Data) -> list[str]:
    s = d.score(WALK_MISS)
    return [word(s["attempts"]), str(s["oversold_runs"]), str(s["caps"]["runs"]), str(s["turns"])]


def walk_prose_big(d: Data) -> list[str]:
    s, haiku = d.score(WALK_BIG), d.score(WALK)
    return [
        str(s["oversold_runs"]),
        str(s["turns"]),
        num(round(s["wall_seconds"] / 60, 1)),
        f"{s['dollars']:.4f}",
        f"{haiku['dollars']:.4f}",
    ]


def walk_prose_caps(d: Data) -> list[str]:
    caps = d.score(WALK)["caps"]
    return [str(caps["runs"]), str(caps["attempts"]), str(caps["turns"])]


def walk_quotes(d: Data) -> list[str]:
    first = min(
        (r for r in records(d, WALK) if r.get("kind") == "prediction"), key=lambda r: r["attempt"]
    )
    sentences = re.split(r"(?<=\.) ", first["hypothesis"])
    events = transcript(d, WALK)
    code = next(
        e["content"]
        for e in events
        if e.get("event") == "tool" and e["content"].startswith(f"{CODE_FILE}, lines 1 to")
    )
    lines = {
        int(n): text
        for n, _, text in (x.strip(" ").partition("\t") for x in code.splitlines()[1:])
        if n.isdigit()
    }
    block = "\n".join(lines[n] for n in CODE_LINES)
    summary = json.loads((d.root / WALK / "claims.json").read_text(encoding="utf-8"))["summary"]
    said = next(s for s in re.split(r"(?<=\.) ", summary) if s.startswith("No claims"))
    return [
        "> " + " ".join(sentences[:2]),
        f"```ts\n{block}\n```",
        f'"{said}"',
        f"{CODE_URL}#L{CODE_LINES[0]}-L{CODE_LINES[-1]}",
    ]


ORDINALS = ("first", "second", "third", "fourth", "fifth")
READ_TOOLS = ("list_files", "read_file", "search")


def walk_prose_tools(d: Data) -> list[str]:
    names = [t["name"] for t in agent.tools_for("v2")]
    return [word(len(names)), word(sum(1 for n in names if n in READ_TOOLS)).capitalize()]


def walk_prose_rules(d: Data) -> list[str]:
    return [word(len(CHECKS))]


def walk_prose_key_read(d: Data) -> list[str]:
    steps = walk_steps(d)
    sent = next(i for i, r in enumerate(steps) if r[1] == "Sent attempt 1")
    before = [r[1] for r in steps[:sent] if r[1].startswith("Read ")]
    return ["last" if before and f"Read `{CODE_FILE}`" in before[-1] else "not the last"]


def walk_prose_excerpt(d: Data) -> list[str]:
    plain = sorted(f.name for f in walk_folders(d, 1)[None])
    folder = d.root / WALK / "runs" / WALK_RUN
    index = next(
        i
        for i, h in enumerate(histories(folder), start=1)
        if any(v["check"] == "no_oversell" and v["result"] == "fail" for v in h["verdicts"])
    )
    return [str(index), ORDINALS[plain.index(WALK_RUN)], WALK_RUN, f"{index:03d}"]


CODE_FILE = "packages/modules/locking/src/providers/in-memory.ts"
CODE_LINES = (16, 17, 18, 19)
CODE_URL = f"https://github.com/medusajs/medusa/blob/v2.22.0/{CODE_FILE}"

QUOTES = {"WALKTHROUGH.md": walk_quotes}

BLOCKS = {
    "WALKTHROUGH.md": [
        ("<summary>The full scenario file</summary>", "yaml", walk_scenario),
        ("<summary>One failing run, as Oversold recorded it</summary>", "json", walk_excerpt),
    ],
}

CHECKED = {
    "README.md": {
        "| Test scenario | Public bug | Rule broken on plain Medusa |": readme_cases,
        "| Test scenario | Haiku 5.5 on v2 | Haiku 5.5, whole budget |": readme_follow,
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
        "| Test scenario | Haiku 5.5 on v2 |": follow_headline,
        "| Arm | Trials | Median runs used |": follow_costs,
        "| Arm | Test | Compared with |": follow_test_rows,
        "| Held trial | Test | Runs |": follow_hand_rows,
        "| Fixed guess, no AI |": results_fixed,
        "| Fix build or Redis run |": negative_rows,
        "| Setting, pooled over every review |": pooled_rows,
    },
    "benchmark/README.md": {
        "| Case | Set | no_oversell 2 |": sets_2004ed5,
        "| Case | 2.22.0 at v0.1.1 |": reproduced_2004ed5,
        "| Case | Version | Set | Locking |": sets_a35d162,
        "| Case | 2.21.2 | 2.19.0 | 2.22.0 |": reproduced_a35d162,
        "| Case | Version | Oversold | Set |": sets_earlier,
        "| Fixed guess | File accepted | Cause accepted |": fixed_guesses,
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
        "| Trial | Model | Prompts |": follow_rows,
    },
    "WALKTHROUGH.md": {
        "| Step | What it did | Why it mattered |": walk_steps,
        "| Saved before any run | Value |": walk_prediction,
        "| Build | Runs | no_oversell |": walk_results,
        "| How it ended | Value |": walk_end,
        "| Attempt | What it tested |": walk_big,
    },
}

SAME_HEADER = {"| Trial | Feedback | Turns |": (unguided_rows, guided2_rows)}


def unknown_prose(d: Data) -> list[str]:
    u = d.unknown_runs()
    every = "every one" if u["oversold_pass"] == u["unknown"] else f"{u['oversold_pass']:,}"
    return [f"{u['unknown']:,}", f"{u['runs']:,}", f"{u['inconclusive']:,}", every]


PROSE = {
    "WALKTHROUGH.md": [
        (
            re.compile(
                r"(\S+) of (\S+) no-feedback Haiku trials reproduced both race scenarios, "
                r"and (\S+) of (\S+) found all three scenarios"
            ),
            walk_prose_found,
        ),
        (re.compile(r"credited at run (\d+)"), walk_prose_run),
        (re.compile(r"The agent could use (\S+) tools\. (\S+) read"), walk_prose_tools),
        (re.compile(r"checked (\S+) rules after every run"), walk_prose_rules),
        (
            re.compile(r"The key read is the (\S+) one before the first attempt"),
            walk_prose_key_read,
        ),
        (
            re.compile(
                r"From \[run (\d+) of the (\S+) plain set\]"
                r"\(benchmark/agent/scale-10/unguided-none-5/runs/(\S+)/run-(\d+)\.json\.gz\)"
            ),
            walk_prose_excerpt,
        ),
        (
            re.compile(r"The trial had at most (\S+) runs, (\S+) attempts and (\S+) turns"),
            walk_prose_caps,
        ),
        (
            re.compile(
                r"It starts (\S+) Medusa servers that share one database, sets the stock of an "
                r"item called SOLO to (\S+) unit"
            ),
            walk_prose_scenario,
        ),
        (
            re.compile(r"It sent (\S+) attempt, used (\S+) of its (\S+) runs and (\S+) turns"),
            walk_prose_miss,
        ),
        (
            re.compile(
                r"It used (\S+) runs and (\S+) turns, took (\S+) minutes and cost \$(\S+), "
                r"against \$(\S+) for the Haiku trial above"
            ),
            walk_prose_big,
        ),
    ],
    "RESULTS.md": [
        (
            re.compile(
                r"(\S+) of Shortfall's (\S+) committed runs had a checkout with an unknown "
                r"outcome, and all (\S+) are marked inconclusive\. In (every one|\S+) of them "
                r"Oversold said pass on all five checks\."
            ),
            unknown_prose,
        )
    ],
}


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
        for pattern, maker in PROSE.get(doc, []):
            matches = list(pattern.finditer(text))
            if not matches:
                out.append(f"{doc}: no line matching {pattern.pattern[:60]!r}")
                continue
            want_all = maker(d)
            for m in matches:
                for k, (got, want) in enumerate(zip(m.groups(), want_all, strict=True), start=1):
                    if got != want:
                        out.append(
                            f"{doc} line {pattern.pattern[:30]!r} value {k}: "
                            f"the doc says {got!r}, the data gives {want!r}"
                        )
        for summary, lang, maker in BLOCKS.get(doc, []):
            at = text.find(summary)
            start = text.find(f"```{lang}\n", at) if at >= 0 else -1
            end = text.find("\n```", start + len(lang) + 4) if start >= 0 else -1
            if end < 0:
                out.append(f"{doc}: no {lang} block after {summary!r}")
            elif text[start + len(lang) + 4 : end] != maker(d):
                out.append(f"{doc}: the {lang} block after {summary!r} does not match the data")
        if doc in QUOTES:
            for quote in QUOTES[doc](d):
                if quote not in text:
                    out.append(f"{doc}: does not hold {quote[:60]!r} as the data gives it")
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
