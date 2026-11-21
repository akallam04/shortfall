import json
import shutil
from pathlib import Path

import pytest
import yaml

from shortfall import coverage, ledger, score, sweep, trials
from shortfall.answers import ACCEPTED, NOT_ACCEPTED, NOT_APPLICABLE
from shortfall.budget import Budget
from shortfall.cases import RULES, Control
from shortfall.control import variant

ROOT = Path(__file__).resolve().parent.parent
HISTORIES = Path(__file__).resolve().parent / "data" / "histories"
CASES = score.load_cases(ROOT / "benchmark" / "cases")
RULES_BY_CASE = {c.id: c.rule for c in CASES.values()}
IMAGE = "sha256:" + "1" * 64
PIN = "a18d5c9f3892dbca86effa0766e975985f8324bd"
CONFIRM = "packages/core/core-flows/src/cart/steps/confirm-inventory.ts"
RESERVE = "packages/core/core-flows/src/cart/steps/reserve-inventory.ts"
LAST_UNIT = "medusa-17032-last-unit"
COUNTER = "medusa-17032-counter"
LINES = "medusa-16502-lines"


def hist(name: str) -> dict:
    return json.loads((HISTORIES / f"{name}.json").read_text(encoding="utf-8"))


def many(*parts: tuple[str, int]) -> list[dict]:
    out = []
    for name, n in parts:
        out += [hist(name) for _ in range(n)]
    return out


class FixtureRunner:
    def __init__(self, queues: dict[str, list[dict]]):
        self.queues = {k: list(v) for k, v in queues.items()}
        self.calls: list[tuple[str, int]] = []

    def run(self, scenario: Path, runs: int, version: str) -> score.RunSet:
        self.calls.append((scenario.stem, runs))
        queue = self.queues[scenario.stem]
        assert len(queue) >= runs, f"{scenario.stem} needs {runs}, has {len(queue)}"
        histories, self.queues[scenario.stem] = queue[:runs], queue[runs:]
        return score.RunSet(folder=f"runs/fixture-{scenario.stem}", histories=histories)


@pytest.fixture
def candidates(tmp_path):
    paths = sweep.write(sweep.grid(0), tmp_path / "runs" / "sweep" / "s")
    return {p.stem.split("-", 2)[2]: p for p in paths}


def queues(path: Path, candidate: list[dict], **controls: list[dict]) -> dict:
    out = {path.stem: candidate}
    for name, items in controls.items():
        out[f"{path.stem}-{name.replace('_', '-')}-control"] = items
    return out


def ledger_file(tmp_path: Path) -> Path:
    return tmp_path / "runs" / "ledger.jsonl"


def make(tmp_path, path, runner, budget, version="2.22.0", named=(None, None), n=1):
    meta = {"attempt_id": f"s-{n:03d}", "source": "sweep", "seed": 0, "rerun_of": None}
    return score.Attempt(
        tmp_path,
        path,
        version,
        runner,
        budget,
        CASES,
        IMAGE,
        "none",
        PIN,
        meta,
        ledger_file(tmp_path),
        named_file=named[0],
        named_cause=named[1],
    )


def sweep_of(tmp_path, items, budget=None, version="2.22.0", named=(None, None)):
    q = {}
    for _, queue in items:
        q.update(queue)
    runner = FixtureRunner(q)
    budget = budget or Budget()
    factories = [
        (lambda path=path, n=n: make(tmp_path, path, runner, budget, version, named, n))
        for n, (path, _) in enumerate(items, start=1)
    ]
    attempts, stop = score.run_attempts(factories, budget, report=lambda line: None)
    records = ledger.load(ledger_file(tmp_path))
    finals = [r for r in records if r["kind"] == "final"]
    for a in attempts:
        ledger.validate(a.entry, legacy=False)
    assert sorted(f["attempt_id"] for f in finals) == sorted(
        a.entry["attempt_id"] for a in attempts
    )
    return attempts, stop, runner, budget


def attempt(tmp_path, path, q, budget=None, version="2.22.0", named=(None, None)):
    attempts, stop, runner, budget = sweep_of(tmp_path, [(path, q)], budget, version, named)
    [a] = attempts
    records = ledger.load(ledger_file(tmp_path))
    spent_runs = sum(r["oversold_runs"] for r in records if r["kind"] == "spend")
    assert spent_runs == a.entry["oversold_runs"] == budget.session_used
    return a.entry, stop, runner, budget


def results(entry: dict) -> tuple:
    return (entry["violation"], entry["reproduced"])


def test_case_map_is_gone_and_cases_are_picked_by_rule():
    assert not hasattr(score, "case_map")
    assert {c.id: (c.rule, c.scoring.variant) for c in CASES.values()} == {
        LINES: ("no_oversell", "pr-16961"),
        COUNTER: ("reserved_matches_reservations", "pr-17420"),
        LAST_UNIT: ("no_oversell", "pr-17420"),
    }


def test_a_clean_candidate_gets_a_second_pass_of_seven_runs(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    entry, stop, runner, _ = attempt(tmp_path, path, queues(path, many(("pass", 10))))
    assert stop is None
    assert entry["violation"] == {
        "result": "not reproduced within 10 runs",
        "rules": {},
        "runs": 10,
    }
    assert entry["reproduced"] == {"cases": {}, "rules": {}}
    assert entry["located"] == {"result": NOT_APPLICABLE}
    assert runner.calls == [(path.stem, 1), (path.stem, 2), (path.stem, 7)]
    assert (entry["screen_runs"], entry["retry_runs"], entry["score_runs"]) == (3, 7, 0)


def test_without_budget_for_a_second_pass_it_stays_at_three_runs(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("pass", 3)))
    entry, stop, runner, _ = attempt(tmp_path, path, q, budget=Budget(session_runs=9))
    assert stop is None
    assert entry["violation"]["result"] == "not reproduced within 3 runs"
    assert runner.calls == [(path.stem, 1), (path.stem, 2)]


def test_the_second_pass_comes_after_every_first_screen(tmp_path, candidates):
    a = candidates["s2-solo-c2-short-together"]
    b = candidates["s2-piece-c2-short-together"]
    c = candidates["s1-solo-c2-short-together"]
    items = [
        (a, queues(a, many(("pass", 10)))),
        (
            b,
            queues(
                b,
                many(("fail-no-oversell-and-reserved", 13)),
                pr_16961=many(("pass", 10)),
                pr_17420=many(("pass", 10)),
            ),
        ),
        (c, queues(c, many(("pass", 10)))),
    ]
    attempts, stop, runner, budget = sweep_of(tmp_path, items)
    assert stop is None
    assert runner.calls == [
        (a.stem, 1),
        (a.stem, 2),
        (b.stem, 1),
        (b.stem, 2),
        (b.stem, 10),
        (f"{b.stem}-pr-16961-control", 10),
        (f"{b.stem}-pr-17420-control", 10),
        (c.stem, 1),
        (c.stem, 2),
        (a.stem, 7),
        (c.stem, 7),
    ]
    assert [x.entry["oversold_runs"] for x in attempts] == [10, 33, 10]
    assert budget.session_used == 53


def test_a_failure_in_the_second_pass_goes_to_scoring(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    candidate = (
        many(("pass", 3))
        + many(("fail-no-oversell-and-reserved", 1), ("pass", 6))
        + many(("fail-no-oversell-and-reserved", 1), ("pass", 9))
    )
    q = queues(
        path,
        candidate,
        pr_16961=many(("fail-no-oversell", 1), ("pass", 9)),
        pr_17420=many(("pass", 10)),
    )
    entry, stop, runner, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["violation"] == {
        "result": "violation",
        "rules": {"no_oversell": 2, "reserved_matches_reservations": 2},
        "runs": 20,
    }
    assert entry["reproduced"]["cases"] == {
        LINES: "not reproduced",
        COUNTER: "reproduced",
        LAST_UNIT: "reproduced",
    }
    assert entry["oversold_runs"] == 40
    assert (entry["screen_runs"], entry["retry_runs"], entry["score_runs"]) == (3, 7, 10)


def test_a_shared_rule_runs_every_control_and_a_shared_control_runs_once(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(
        path,
        many(("fail-no-oversell-and-reserved", 1), ("pass", 2))
        + many(("fail-no-oversell-and-reserved", 1), ("pass", 9)),
        pr_16961=many(("fail-no-oversell", 1), ("pass", 9)),
        pr_17420=many(("pass", 10)),
    )
    entry, stop, runner, _ = attempt(tmp_path, path, q)
    assert stop is None
    controls = [(c["control"], c["cases"], c["runs"]) for c in entry["controls"]]
    assert controls == [
        ("pr-16961-control", [LINES], 10),
        ("pr-17420-control", [LAST_UNIT, COUNTER], 10),
    ]
    assert [call for call in runner.calls if call[0].endswith("pr-17420-control")] == [
        (f"{path.stem}-pr-17420-control", 10)
    ]
    assert entry["reproduced"] == {
        "cases": {LINES: "not reproduced", COUNTER: "reproduced", LAST_UNIT: "reproduced"},
        "rules": {"no_oversell": "reproduced", "reserved_matches_reservations": "reproduced"},
    }
    control = path.with_name(f"{path.stem}-pr-17420-control.yaml").read_text(encoding="utf-8")
    assert control == variant(path.read_text(encoding="utf-8"), "pr-17420", "2.22.0")


def test_a_two_server_failure_is_credited_to_the_bug_its_control_clears(tmp_path, candidates):
    path = candidates["s2-piece-twopack-c2-short-together"]
    q = queues(
        path,
        many(("fail-no-oversell", 13)),
        pr_16961=many(("pass", 10)),
        pr_17420=many(("fail-no-oversell", 10)),
    )
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["servers"] == 2
    assert entry["reproduced"] == {
        "cases": {LINES: "reproduced", LAST_UNIT: "not reproduced"},
        "rules": {"no_oversell": "reproduced"},
    }


def test_a_one_server_failure_is_credited_to_the_bug_its_control_clears(tmp_path, candidates):
    path = candidates["s1-piece-twopack-c2-short-together"]
    q = queues(
        path,
        many(("fail-no-oversell", 13)),
        pr_16961=many(("pass", 10)),
        pr_17420=many(("fail-no-oversell", 10)),
    )
    entry, stop, _, _ = attempt(tmp_path, path, q, named=(CONFIRM, "per-line-check"))
    assert stop is None
    assert entry["servers"] == 1
    assert entry["reproduced"]["cases"] == {LINES: "reproduced", LAST_UNIT: "not reproduced"}
    assert entry["located"] == {
        "result": "graded",
        "file": CONFIRM,
        "cause": "per-line-check",
        "cases": {LINES: {"file": ACCEPTED, "cause": ACCEPTED, "located": ACCEPTED}},
    }


def test_a_one_server_oversell_the_16502_fix_leaves_stops_the_sweep(tmp_path, candidates):
    path = candidates["s1-piece-twopack-c2-short-together"]
    q = queues(
        path,
        many(("fail-no-oversell", 13)),
        pr_16961=many(("fail-no-oversell", 10)),
        pr_17420=many(("pass", 10)),
    )
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop.startswith("uncovered failure: no_oversell failed 10 of 10 runs in the pr-16961")
    assert entry["controls"] == []
    assert entry["violation"]["result"] == "violation"


def test_a_named_file_outside_the_answer_is_not_accepted(tmp_path, candidates):
    path = candidates["s2-piece-twopack-c2-short-together"]
    q = queues(
        path,
        many(("fail-no-oversell", 13)),
        pr_16961=many(("pass", 10)),
        pr_17420=many(("fail-no-oversell", 10)),
    )
    entry, _, _, _ = attempt(tmp_path, path, q, named=(RESERVE, "per-line-check"))
    assert entry["located"]["cases"] == {
        LINES: {"file": NOT_ACCEPTED, "cause": ACCEPTED, "located": NOT_ACCEPTED}
    }


def test_inventory_module_with_the_wrong_cause_is_not_located(tmp_path, candidates):
    path = candidates["s2-piece-twopack-c2-short-together"]
    q = queues(
        path,
        many(("fail-no-oversell", 13)),
        pr_16961=many(("pass", 10)),
        pr_17420=many(("fail-no-oversell", 10)),
    )
    inventory = "packages/modules/inventory/src/services/inventory-module.ts"
    entry, _, _, _ = attempt(tmp_path, path, q, named=(inventory, "process-local-lock"))
    assert entry["located"]["cases"] == {
        LINES: {"file": ACCEPTED, "cause": NOT_ACCEPTED, "located": NOT_ACCEPTED}
    }


def test_a_rule_no_control_clears_is_a_violation_with_cause_not_isolated(tmp_path, candidates):
    path = candidates["s2-piece-c2-short-together"]
    q = queues(
        path,
        many(("fail-reserved", 13)),
        pr_17420=many(("fail-reserved", 1), ("pass", 9)),
    )
    entry, stop, runner, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["violation"]["result"] == "violation"
    assert entry["reproduced"] == {
        "cases": {COUNTER: "not reproduced"},
        "rules": {"reserved_matches_reservations": score.NOT_ISOLATED},
    }
    assert score.NOT_ISOLATED == "violation, cause not isolated"
    assert len(runner.calls) == 4


def test_an_inconclusive_control_run_blocks_reproduction(tmp_path, candidates):
    path = candidates["s2-piece-c2-short-together"]
    q = queues(
        path,
        many(("fail-reserved", 13)),
        pr_17420=many(("inconclusive", 1), ("pass", 9)),
    )
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["reproduced"] == {
        "cases": {COUNTER: "inconclusive"},
        "rules": {"reserved_matches_reservations": "inconclusive"},
    }
    assert entry["inconclusive"]["control"] == 1


def test_a_failure_seen_only_in_the_screen_is_not_isolated(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("fail-no-oversell-and-reserved", 1), ("pass", 12)))
    entry, stop, runner, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["violation"]["rules"] == {"no_oversell": 1, "reserved_matches_reservations": 1}
    assert entry["reproduced"] == {
        "cases": {},
        "rules": {
            "no_oversell": score.NOT_ISOLATED,
            "reserved_matches_reservations": score.NOT_ISOLATED,
        },
    }
    assert runner.calls == [(path.stem, 1), (path.stem, 2), (path.stem, 10)]


def test_on_another_version_there_is_no_scoring_control(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("fail-no-oversell-and-reserved", 13)))
    entry, stop, runner, _ = attempt(tmp_path, path, q, version="2.21.2")
    assert stop is None
    assert entry["reproduced"]["cases"] == {
        LINES: "no scoring control on 2.21.2",
        COUNTER: "no scoring control on 2.21.2",
        LAST_UNIT: "no scoring control on 2.21.2",
    }
    assert set(entry["reproduced"]["rules"].values()) == {score.NOT_ISOLATED}
    assert len(runner.calls) == 3


@pytest.mark.parametrize("field", ["variant", "locking"])
def test_a_candidate_that_sets_variant_or_locking_is_refused(tmp_path, candidates, field):
    source = candidates["s2-solo-c2-short-together"]
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    data["target"][field] = "pr-17420" if field == "variant" else "redis"
    path = source.with_name("own-control.yaml")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    runner = FixtureRunner({})
    with pytest.raises(score.CandidateRefused, match=f"may not set target.{field}"):
        make(tmp_path, path, runner, Budget())
    assert not ledger_file(tmp_path).exists()
    with pytest.raises(score.CandidateRefused, match="target mapping"):
        score.check_candidate({"name": "x"})


def test_setup_failure_on_the_first_run_is_unpreparable(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    entry, stop, runner, _ = attempt(tmp_path, path, queues(path, many(("setup-failed", 1))))
    assert stop is None
    assert entry["violation"]["result"] == "unpreparable"
    assert entry["setup_error"].startswith("prepare cart ")
    assert runner.calls == [(path.stem, 1)]


def test_setup_failure_later_in_the_screen_is_unpreparable(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("pass", 1), ("setup-failed", 1), ("pass", 1)))
    entry, stop, runner, _ = attempt(tmp_path, path, q)
    assert entry["violation"] == {"result": "unpreparable", "rules": {}, "runs": 3}
    assert runner.calls == [(path.stem, 1), (path.stem, 2)]


def test_a_harness_error_outside_cart_setup_is_not_unpreparable(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    entry, stop, _, _ = attempt(tmp_path, path, queues(path, many(("inconclusive", 10))))
    assert entry["violation"]["result"] == "inconclusive"
    assert entry["setup_error"] is None
    assert entry["inconclusive"] == {"screen": 3, "retry": 7, "score": 0, "control": 0}


def test_a_partly_inconclusive_clean_candidate_is_not_reproduced(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("inconclusive", 1), ("pass", 9)))
    entry, _, _, _ = attempt(tmp_path, path, q)
    assert entry["violation"]["result"] == "not reproduced within 10 runs"
    assert entry["inconclusive"]["screen"] == 1


def test_an_uncovered_rule_stops_the_sweep(tmp_path, candidates):
    path = candidates["s1-solo-c2-short-together"]
    q = queues(path, many(("constructed-fail-one-order", 3)))
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop.startswith("uncovered failure: one_order_per_cart failed 1 of 1 runs")
    assert entry["violation"]["result"] == "violation"


def test_one_order_per_cart_on_two_in_memory_servers_does_not_stop_the_sweep(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("constructed-fail-one-order", 13)))
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["violation"]["result"] == "violation"
    assert entry["manual_check"] == [
        "one_order_per_cart failed 13 of 13 runs on plain Medusa 2.22.0: violation, cause "
        "not isolated, no case's scoring control clears it",
    ]


def held_list(root: Path, *entries: dict) -> None:
    path = root / coverage.HELD_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in entries))


def missing_order_entry(path: Path, **over) -> dict:
    data = yaml.safe_load(path.read_text())
    entry = {
        "rule": "no_missing_orders",
        "shape": {"servers": 2, "carts": 2, "locking": "in-memory", "variant": None},
        "race": [{"do": step["do"], "server": step["server"]} for step in data["race"]],
    }
    entry.update(over)
    return entry


def test_a_shape_on_the_local_held_list_is_held_not_stopped(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    held_list(tmp_path, missing_order_entry(path))
    q = queues(path, [missing_order()] * 3 + many(("pass", 10)))
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["violation"]["result"] == "violation"
    assert entry["manual_check"][0] == (
        "held shape: no_missing_orders failed 3 of 3 runs in the screen set, "
        "a shape on the local held list"
    )
    assert any(n.startswith(trials.HOLDS) for n in entry["manual_check"])


@pytest.mark.parametrize(
    "over",
    [
        {"rule": "no_oversell"},
        {"shape": {"servers": 2, "carts": 2, "locking": "redis"}},
        {"race": [{"do": "complete", "server": 1}]},
    ],
)
def test_the_held_list_matches_only_its_exact_shape(tmp_path, candidates, over):
    path = candidates["s2-solo-c2-short-together"]
    held_list(tmp_path, missing_order_entry(path, **over))
    _, stop, _, _ = attempt(tmp_path, path, queues(path, [missing_order()] * 3))
    assert stop.startswith("uncovered failure: no_missing_orders failed 1 of 1 runs")


def test_one_server_single_line_oversell_is_uncovered(tmp_path, candidates):
    path = candidates["s1-solo-c2-short-together"]
    entry, stop, _, _ = attempt(tmp_path, path, queues(path, many(("fail-no-oversell", 3))))
    assert stop.startswith("uncovered failure: no_oversell")


def test_a_missing_order_failure_is_outside_the_coverage_map(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    entry, stop, _, _ = attempt(tmp_path, path, queues(path, [missing_order()] * 3))
    assert stop.startswith("uncovered failure: no_missing_orders failed 1 of 1 runs")
    assert entry["check_versions"]["no_missing_orders"] == [1]
    assert entry["check_versions"]["no_oversell"] == [2]


def test_the_ledger_records_check_versions(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    entry, stop, _, _ = attempt(tmp_path, path, queues(path, many(("pass", 10))))
    assert entry["check_versions"] == {rule: [1] for rule in RULES[:4]}
    assert ledger.load(ledger_file(tmp_path))[-1]["check_versions"] == entry["check_versions"]


def test_session_cap_mid_screen_stops_cleanly(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    runner = FixtureRunner(queues(path, many(("pass", 3))))
    budget = Budget(session_runs=2)
    a = make(tmp_path, path, runner, budget)
    a.first_pass()
    entry = a.finish()
    assert a.stop.startswith("session runs cap reached")
    assert entry["oversold_runs"] == 1
    assert entry["violation"]["result"] == "not reproduced within 1 runs"


def test_session_cap_before_scoring_stops_cleanly(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("fail-no-oversell-and-reserved", 3)))
    entry, stop, runner, _ = attempt(tmp_path, path, q, budget=Budget(session_runs=10))
    assert stop.startswith("session runs cap reached")
    assert entry["violation"]["result"] == "violation"
    assert set(entry["reproduced"]["rules"].values()) == {score.CUT_OFF}
    assert entry["manual_check"] == []
    assert entry["oversold_runs"] == 3


def test_attempt_cap_ends_only_that_attempt(tmp_path, candidates):
    a = candidates["s2-solo-c2-short-together"]
    b = candidates["s2-piece-c2-short-together"]
    items = [
        (
            a,
            queues(
                a,
                many(("fail-no-oversell-and-reserved", 13)),
                pr_16961=many(("pass", 10)),
                pr_17420=many(("pass", 10)),
            ),
        ),
        (b, queues(b, many(("pass", 10)))),
    ]
    attempts, stop, runner, _ = sweep_of(tmp_path, items, budget=Budget(attempt_runs=25))
    assert stop is None
    first, second = attempts
    assert first.entry["stop_reason"].startswith("attempt runs cap reached")
    assert first.entry["oversold_runs"] == 23
    assert first.entry["reproduced"]["cases"] == {LINES: "reproduced"}
    assert second.entry["violation"]["result"] == "not reproduced within 10 runs"


def test_interleaved_attempts_keep_their_own_run_counts(tmp_path, candidates):
    a = candidates["s2-solo-c2-short-together"]
    b = candidates["s2-piece-c2-short-together"]
    items = [
        (a, queues(a, many(("pass", 10)))),
        (b, queues(b, many(("fail-reserved", 13)), pr_17420=many(("pass", 10)))),
    ]
    attempts, _, _, budget = sweep_of(tmp_path, items)
    assert [x.entry["oversold_runs"] for x in attempts] == [10, 23]
    assert budget.session_used == 33
    spends = {}
    for r in ledger.load(ledger_file(tmp_path)):
        if r["kind"] == "spend":
            spends[r["attempt_id"]] = spends.get(r["attempt_id"], 0) + r["oversold_runs"]
    assert spends == {"s-001": 10, "s-002": 23}


class KilledRunner(FixtureRunner):
    def __init__(self, queues, die_on_call: int):
        super().__init__(queues)
        self.die_on_call = die_on_call

    def run(self, scenario, runs, version):
        if len(self.calls) + 1 == self.die_on_call:
            self.calls.append((scenario.stem, runs))
            raise KeyboardInterrupt
        return super().run(scenario, runs, version)


def test_a_killed_attempt_still_shows_its_spend(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    runner = KilledRunner(queues(path, many(("fail-no-oversell-and-reserved", 13))), 3)
    budget = Budget()
    with pytest.raises(KeyboardInterrupt):
        score.run_attempts([lambda: make(tmp_path, path, runner, budget)], budget)
    records = ledger.load(ledger_file(tmp_path))
    assert [r["kind"] for r in records] == ["started", "spend", "spend", "spend"]
    assert [r["set"] for r in records[1:]] == ["screen", "screen", "score"]
    [a] = ledger.attempts(records)
    assert a["interrupted"] is True
    assert a["oversold_runs"] == 13


def test_each_run_set_is_in_the_ledger_before_it_runs(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    seen = []

    class Watching(FixtureRunner):
        def run(self, scenario, runs, version):
            records = ledger.load(ledger_file(tmp_path))
            seen.append(sum(r["oversold_runs"] for r in records if r["kind"] == "spend"))
            return super().run(scenario, runs, version)

    runner = Watching(queues(path, many(("pass", 10))))
    budget = Budget()
    score.run_attempts([lambda: make(tmp_path, path, runner, budget)], budget, report=print)
    assert seen == [1, 3, 10]


def test_cap_before_the_first_run_writes_started_and_final_with_no_spend(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    runner = FixtureRunner(queues(path, []))
    a = make(tmp_path, path, runner, Budget(session_runs=0))
    a.first_pass()
    entry = a.finish()
    assert [r["kind"] for r in ledger.load(ledger_file(tmp_path))] == ["started", "final"]
    assert entry["violation"] == {"result": "inconclusive", "rules": {}, "runs": 0}
    assert entry["oversold_runs"] == 0


def test_orphaned_order_failure_is_flagged_for_a_manual_check(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, many(("constructed-fail-orphaned", 13)))
    entry, stop, runner, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["manual_check"] == [
        "no_orphaned_orders failed 3 of 3 runs in the screen set, covered only by "
        "https://github.com/medusajs/medusa/issues/16825, which Oversold has never reproduced",
        "no_orphaned_orders failed 10 of 10 runs in the score set, covered only by "
        "https://github.com/medusajs/medusa/issues/16825, which Oversold has never reproduced",
        "no_orphaned_orders failed 13 of 13 runs on plain Medusa 2.22.0: violation, cause "
        "not isolated, no case's scoring control clears it",
    ]
    assert entry["reproduced"]["rules"] == {"no_orphaned_orders": score.NOT_ISOLATED}
    assert entry["controls"] == []


def test_a_run_with_no_lock_calls_stops_the_sweep(tmp_path, candidates):
    path = candidates["s2-piece-c2-short-together"]
    q = queues(path, many(("fail-reserved", 13)), pr_17420=[no_lock_calls()] * 10)
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop.startswith(
        "error: harness: 10 of 10 runs in the pr-17420-control set made no lock calls"
    )
    assert score.lock_error(no_lock_calls()).startswith("redis locking: ")
    assert score.setup_error(no_lock_calls()) is None


def test_an_image_label_harness_error_stops_the_sweep(tmp_path, candidates):
    path = candidates["s2-piece-c2-short-together"]
    q = queues(path, many(("fail-reserved", 13)), pr_17420=[image_mismatch()] * 10)
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop.startswith(
        "error: harness: 10 of 10 runs in the pr-17420-control set had an image or variant"
    )


def test_control_builder_picks_by_kind_and_version():
    lines = CASES[LINES].scoring
    assert score.control_builder(lines, "2.22.0")[0] == "pr-16961-control"
    assert score.control_builder(CASES[COUNTER].scoring, "2.22.0")[0] == "pr-17420-control"
    assert score.control_builder(lines, "2.21.2") is None
    redis = Control(kind="redis-locking", file="redis-control.yaml")
    assert score.control_builder(redis, "2.19.0")[0] == "redis-control"
    one = Control(kind="one-server", file="one-server-control.yaml")
    assert score.control_builder(one, "2.19.0")[0] == "control"
    assert score.control_builder(None, "2.22.0") is None


def test_a_variant_scenario_has_no_variant_control():
    folder = ROOT / "benchmark" / "cases" / LINES
    _, build = score.control_builder(CASES[LINES].scoring, "2.22.0")
    assert (
        build((folder / "reference.yaml").read_text())
        == (folder / "pr-16961-control.yaml").read_text()
    )
    with pytest.raises(ValueError, match="already has target.variant"):
        build((folder / "pr-16961-control.yaml").read_text())


class FakeOversold:
    queues: dict = {}

    def __init__(self, root):
        self.pin = PIN
        self.runner = FixtureRunner(self.queues)

    def image(self, version):
        return IMAGE, "none"

    def run(self, scenario, runs, version):
        return self.runner.run(scenario, runs, version)


def sweep_setup(tmp_path, monkeypatch, outcomes, per=3):
    shutil.copytree(
        ROOT / "benchmark" / "cases",
        tmp_path / "benchmark" / "cases",
        ignore=shutil.ignore_patterns("results"),
    )
    paths = sweep.write(sweep.grid(0)[: len(outcomes)], tmp_path / "runs" / "sweep" / "s")
    FakeOversold.queues = {p.stem: many((o, per)) for p, o in zip(paths, outcomes, strict=True)}
    monkeypatch.setattr(score, "OversoldRunner", FakeOversold)
    return paths


def test_run_sweep_stops_at_the_session_cap_and_writes_every_attempt(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["pass"] * 5)
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s", max_runs=10) == 0
    entries = ledger.attempts(ledger.load(tmp_path / "runs" / "ledger.jsonl"))
    assert [e["attempt_id"] for e in entries] == ["s-001", "s-002", "s-003"]
    assert {e["violation"]["result"] for e in entries} == {"not reproduced within 3 runs"}
    out = capsys.readouterr().out
    assert "5 candidates, 0 refused, 3 attempted, 3 screened, 0 retried, 0 scored, 2 skipped" in out
    assert '"not reproduced within 3 runs": 3' in out
    assert "session runs: used 9 of 10" in out


def test_run_sweep_gives_clean_candidates_a_second_pass(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["pass"] * 2, per=10)
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s") == 0
    out = capsys.readouterr().out
    assert "2 candidates, 0 refused, 2 attempted, 2 screened, 2 retried, 0 scored" in out
    assert '"not reproduced within 10 runs": 2' in out


def test_run_sweep_lists_refused_candidates(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["pass"] * 3, per=10)
    data = yaml.safe_load(paths[1].read_text(encoding="utf-8"))
    data["target"]["locking"] = "redis"
    paths[1].write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s") == 0
    out = capsys.readouterr().out
    assert f"sweep: refused: {paths[1].stem}: a candidate may not set target.locking" in out
    assert "3 candidates, 1 refused, 2 attempted" in out
    ids = [r["attempt_id"] for r in ledger.load(tmp_path / "runs" / "ledger.jsonl")]
    assert "s-002" not in ids


def test_three_inconclusive_attempts_in_a_row_stop_the_sweep(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["inconclusive"] * 5)
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s") == 0
    entries = ledger.attempts(ledger.load(tmp_path / "runs" / "ledger.jsonl"))
    assert len(entries) == 3
    assert {e["violation"]["result"] for e in entries} == {"inconclusive"}
    out = capsys.readouterr().out
    assert "stopped: harness: 3 attempts in a row had only inconclusive runs" in out
    assert "0 retried" in out


def test_unpreparable_candidates_do_not_stop_the_sweep(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["setup-failed"] * 4)
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s") == 0
    entries = ledger.attempts(ledger.load(tmp_path / "runs" / "ledger.jsonl"))
    assert [e["violation"]["result"] for e in entries] == ["unpreparable"] * 4
    assert "stopped" not in capsys.readouterr().out


def test_run_sweep_lists_manual_checks(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["constructed-fail-orphaned"], per=13)
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s") == 0
    out = capsys.readouterr().out
    assert "sweep: manual check: s-001" in out
    summary = json.loads(out[out.index("\n{") + 1 : out.index("\nsweep: trial summary")])
    assert summary["violation"] == {"violation": 1}
    assert summary[score.NOT_ISOLATED] == {"no_orphaned_orders": 1}
    assert summary["located"] == {"not applicable": 1}


def no_lock_calls() -> dict:
    h = hist("pass")
    h["harness_error"] = (
        "redis locking: Medusa made no scripted lock calls during the race, so the servers "
        "did not lock through Redis"
    )
    for v in h["verdicts"]:
        v["result"] = "inconclusive"
        v["reason"] = "harness error: " + h["harness_error"]
    return h


def test_a_redis_locking_history_reads_like_any_other():
    h = hist("redis-locking-pass")
    assert h["target"]["locking"] == "redis"
    assert h["race"]["lock_calls"] > 0
    assert set(h["race"]["redis_command_stats"]) == {"before", "after"}
    c = score.counts([h])
    assert {rule: c[rule]["pass"] for rule in c} == dict.fromkeys(c, 1)
    assert score.inconclusive_runs([h]) == 0
    assert score.setup_error(h) is None
    assert score.lock_error(h) is None
    pin = h["oversold"]["commit"]
    [image] = {s["image_id"] for s in h["target"]["servers"]}
    score.check_histories([h], 1, pin, image)
    with pytest.raises(RuntimeError, match="not sha256:"):
        score.check_histories([h], 1, pin, IMAGE)
    with pytest.raises(RuntimeError, match="pinned Oversold commit"):
        score.check_histories([h], 1, PIN, image)
    with pytest.raises(RuntimeError, match="expected 2 histories"):
        score.check_histories([h], 2, pin, image)


def test_a_variant_history_reads_like_any_other():
    h = hist("pr-16961-stock-drop")
    target = h["target"]
    assert target["variant"]["name"] == "pr-16961"
    assert h["stock_before_race"] == {"WIDGET": 6}
    assert {s["image_inputs"] for s in target["servers"]} == {target["image_inputs"]}
    c = score.counts([h])
    assert {rule: c[rule]["pass"] for rule in c} == dict.fromkeys(c, 1)
    assert score.inconclusive_runs([h]) == 0
    assert score.setup_error(h) is None
    assert score.lock_error(h) is None
    assert score.image_error(h) is None
    [image] = {s["image_id"] for s in target["servers"]}
    score.check_histories([h], 1, h["oversold"]["commit"], image)


def test_a_label_or_replaced_file_mismatch_is_refused():
    h = hist("pr-16961-stock-drop")
    pin = h["oversold"]["commit"]
    h["target"]["servers"][0]["image_inputs"] = "0" * 64
    with pytest.raises(RuntimeError, match="image inputs"):
        score.check_histories([h], 1, pin, None)
    h = hist("pr-16961-stock-drop")
    h["target"]["servers"][0]["variant_files"][0]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="replaced files"):
        score.check_histories([h], 1, pin, None)
    h = hist("pr-16961-stock-drop")
    del h["target"]["servers"][0]["variant_files"]
    with pytest.raises(RuntimeError, match="replaced files"):
        score.check_histories([h], 1, pin, None)
    old = hist("redis-locking-pass")
    assert "image_inputs" not in old["target"]
    score.check_histories([old], 1, old["oversold"]["commit"], None)


def image_mismatch() -> dict:
    h = hist("pass")
    h["harness_error"] = (
        'medusa runs an image with oversold.image-inputs "", this run set\'s image inputs are '
        + "a" * 64
    )
    for v in h["verdicts"]:
        v["result"] = "inconclusive"
        v["reason"] = "harness error: " + h["harness_error"]
    return h


def test_a_cart_setup_error_about_a_variant_is_not_an_image_error():
    h = hist("setup-failed")
    assert "variant" in json.dumps(h)
    assert score.setup_error(h)
    assert score.image_error(h) is None


def test_shape_records_the_variant():
    data = yaml.safe_load((ROOT / "benchmark/cases/medusa-16502-lines/reference.yaml").read_text())
    assert score.shape(data)["variant"] is None
    data["target"]["variant"] = "pr-16961"
    assert score.shape(data)["variant"] == "pr-16961"


def test_five_checks_and_their_versions_come_from_the_verdicts():
    h = hist("five-checks-fail")
    assert [(v["check"], v["version"]) for v in h["verdicts"]] == [
        ("no_oversell", 2),
        ("reserved_matches_reservations", 2),
        ("one_order_per_cart", 2),
        ("no_orphaned_orders", 2),
        ("no_missing_orders", 1),
    ]
    c = score.counts([h, hist("pass")])
    assert list(c) == list(RULES)
    assert c["no_missing_orders"] == {"fail": 0, "pass": 1, "inconclusive": 0}
    assert c["no_oversell"] == {"fail": 1, "pass": 1, "inconclusive": 0}
    assert score.check_versions([h, hist("pass")]) == {
        "no_oversell": [1, 2],
        "reserved_matches_reservations": [1, 2],
        "one_order_per_cart": [1, 2],
        "no_orphaned_orders": [1, 2],
        "no_missing_orders": [1],
    }
    assert score.failed_rules(c) == ["no_oversell", "reserved_matches_reservations"]


def test_an_unknown_check_name_is_counted_and_sorted_last():
    h = hist("five-checks-fail")
    h["verdicts"].append({"check": "a_future_check", "version": 3, "result": "fail"})
    c = score.counts([h])
    assert list(c)[-1] == "a_future_check"
    assert score.check_versions([h])["a_future_check"] == [3]


def missing_order() -> dict:
    h = hist("five-checks-fail")
    for v in h["verdicts"]:
        v["result"] = "fail" if v["check"] == "no_missing_orders" else "pass"
    return h


def test_shape_records_the_locking_mode():
    cases = ROOT / "benchmark" / "cases"
    for case in ("medusa-17032-last-unit", "medusa-17032-counter"):
        ref = yaml.safe_load((cases / case / "reference.yaml").read_text())
        redis = yaml.safe_load((cases / case / "redis-control.yaml").read_text())
        assert score.shape(ref)["locking"] == "in-memory"
        assert score.shape(redis)["locking"] == "redis"


def test_a_candidate_that_sets_checks_is_refused(tmp_path, candidates):
    source = candidates["s2-solo-c2-short-together"]
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    data["checks"] = ["no_oversell"]
    path = source.with_name("own-checks.yaml")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    with pytest.raises(score.CandidateRefused, match="may not set checks"):
        make(tmp_path, path, FixtureRunner({}), Budget())
    assert not ledger_file(tmp_path).exists()


def test_no_reference_control_or_generated_candidate_sets_checks():
    files = sorted((ROOT / "benchmark" / "cases").glob("*/*.yaml"))
    scenarios = [f for f in files if f.name not in ("case.yaml", "answer.yaml")]
    assert len(scenarios) == 10
    texts = [f.read_text(encoding="utf-8") for f in scenarios]
    texts += [sweep.to_yaml(c) for c in sweep.grid(0) + sweep.random_candidates(3, 20)]
    assert len(texts) == 10 + 32 + 20
    for text in texts:
        assert "checks" not in yaml.safe_load(text)


def unknown_call(name: str) -> dict:
    h = hist(name)
    h["operations"] = [
        {"id": 1, "phase": "race", "step": "complete_cart", "cart": "a", "outcome": "ok"},
        {"id": 2, "phase": "race", "step": "complete_cart", "cart": "b", "outcome": "unknown"},
    ]
    return h


def test_a_run_with_an_unknown_complete_call_is_inconclusive():
    h = hist("five-checks-fail")
    assert not score.unknown_completion(h)
    assert score.counts([h])["no_oversell"]["fail"] == 1
    calls = [op for op in h["operations"] if op["step"] == "complete_cart"]
    calls[-1]["outcome"] = "unknown"
    assert score.unknown_completion(h)
    c = score.counts([h])
    assert {rule: row["inconclusive"] for rule, row in c.items()} == dict.fromkeys(RULES, 1)
    assert score.failed_rules(c) == []
    assert score.inconclusive_runs([h, hist("pass")]) == 1
    setup = {"operations": [{"step": "create_cart", "outcome": "unknown"}]}
    assert not score.unknown_completion(setup)


def test_unknown_complete_calls_in_the_candidate_are_not_clean(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, [unknown_call("fail-no-oversell-and-reserved")] * 3 + many(("pass", 7)))
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["violation"] == {
        "result": "not reproduced within 10 runs",
        "rules": {},
        "runs": 10,
    }
    assert entry["inconclusive"]["screen"] == 3


def test_a_candidate_with_only_unknown_complete_calls_is_inconclusive(tmp_path, candidates):
    path = candidates["s2-solo-c2-short-together"]
    entry, _, _, _ = attempt(tmp_path, path, queues(path, [unknown_call("pass")] * 10))
    assert entry["violation"]["result"] == "inconclusive"


def test_unknown_complete_calls_in_a_control_block_reproduction(tmp_path, candidates):
    path = candidates["s2-piece-c2-short-together"]
    q = queues(
        path,
        many(("fail-reserved", 13)),
        pr_17420=[unknown_call("pass")] + many(("pass", 9)),
    )
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["reproduced"]["cases"] == {COUNTER: "inconclusive"}
    assert entry["inconclusive"]["control"] == 1


def test_a_cause_not_isolated_always_goes_to_the_manual_checks(tmp_path, candidates):
    path = candidates["s2-piece-c2-short-together"]
    q = queues(path, many(("fail-reserved", 13)), pr_17420=many(("fail-reserved", 10)))
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert stop is None
    assert entry["reproduced"]["rules"] == {"reserved_matches_reservations": score.NOT_ISOLATED}
    assert entry["manual_check"] == [
        "reserved_matches_reservations failed 13 of 13 runs on plain Medusa 2.22.0: violation, "
        "cause not isolated, no case's scoring control clears it"
    ]


def test_a_reproduced_rule_needs_no_manual_check(tmp_path, candidates):
    path = candidates["s2-piece-c2-short-together"]
    q = queues(path, many(("fail-reserved", 13)), pr_17420=many(("pass", 10)))
    entry, _, _, _ = attempt(tmp_path, path, q)
    assert entry["reproduced"]["rules"] == {"reserved_matches_reservations": "reproduced"}
    assert entry["manual_check"] == []


def test_the_coverage_map_still_stops_before_any_manual_check(tmp_path, candidates):
    path = candidates["s1-solo-c2-short-together"]
    entry, stop, _, _ = attempt(tmp_path, path, queues(path, many(("fail-no-oversell", 3))))
    assert stop.startswith("uncovered failure: no_oversell")
    assert entry["reproduced"]["rules"] == {"no_oversell": score.NOT_ISOLATED}
    assert entry["manual_check"][-1].endswith("no case's scoring control clears it")


def test_run_sweep_lists_causes_not_isolated(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["fail-reserved"], per=13)
    stem = paths[0].stem
    FakeOversold.queues[f"{stem}-pr-17420-control"] = many(("fail-reserved", 10))
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s") == 0
    out = capsys.readouterr().out
    assert (
        f"sweep: manual check: s-001 {stem}: reserved_matches_reservations failed 13 of 13 runs "
        "on plain Medusa 2.22.0: violation, cause not isolated" in out
    )


def test_the_candidate_list_hash_covers_names_text_and_order(tmp_path):
    paths = sweep.write(sweep.ordered(sweep.grid(0), 1), tmp_path / "a")
    first = score.candidate_list_sha256(paths)
    assert first == score.candidate_list_sha256(paths)
    assert first != score.candidate_list_sha256(list(reversed(paths)))
    paths[0].write_text(paths[0].read_text() + "# changed\n")
    assert first != score.candidate_list_sha256(paths)
    import hashlib

    h = hashlib.sha256()
    for p in sweep.write(sweep.ordered(sweep.grid(0), 1), tmp_path / "b"):
        h.update(f"{p.stem}\n{p.read_text()}\n".encode())
    assert h.hexdigest() == first


def test_a_trial_line_freezes_the_list_before_any_run(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["pass"] * 3, per=10)
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s", max_runs=300, order_seed=2) == 0
    records = ledger.load(tmp_path / "runs" / "ledger.jsonl")
    assert records[0]["kind"] == "trial"
    trial = records[0]
    assert trial["candidates"] == 3
    assert trial["candidate_names"] == [p.stem for p in paths]
    assert trial["candidates_sha256"] == score.candidate_list_sha256(paths)
    assert (trial["mode"], trial["order_seed"], trial["run_cap"]) == ("grid", 2, 300)
    assert records[1]["kind"] == "started"
    out = capsys.readouterr().out
    assert f"list sha256 {trial['candidates_sha256']}, run cap 300" in out


def test_reproduced_at_records_the_trial_runs_so_far(tmp_path, candidates):
    a = candidates["s2-solo-c2-short-together"]
    b = candidates["s2-piece-c2-short-together"]
    items = [
        (a, queues(a, many(("pass", 10)))),
        (b, queues(b, many(("fail-reserved", 13)), pr_17420=many(("pass", 10)))),
    ]
    attempts, _, _, _ = sweep_of(tmp_path, items)
    assert attempts[0].entry["reproduced_at"] == {}
    assert attempts[1].entry["reproduced_at"] == {COUNTER: 3 + 23}


def test_trial_summary(tmp_path, monkeypatch, capsys):
    paths = sweep_setup(tmp_path, monkeypatch, ["fail-reserved", "pass", "pass"], per=13)
    FakeOversold.queues[f"{paths[0].stem}-pr-17420-control"] = many(("pass", 10))
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s", max_runs=33) == 0
    records = ledger.load(tmp_path / "runs" / "ledger.jsonl")
    summary = score.trial_summary(records, RULES_BY_CASE)
    assert summary["cases"] == {
        LINES: {"reproduced": False, "runs_to_first": None},
        COUNTER: {"reproduced": True, "runs_to_first": 23},
        LAST_UNIT: {"reproduced": False, "runs_to_first": None},
    }
    assert summary["cases_reproduced"] == 1
    assert summary["runs_used"] == 23 + 3 + 3
    assert (summary["candidates"], summary["reached"], summary["never_reached"]) == (3, 3, 0)
    assert (summary["violations"], summary["cause_not_isolated"]) == (1, 0)
    assert summary["not_reproduced"] == 2
    assert summary["located"] == "not applicable"
    out = capsys.readouterr().out
    assert (
        json.loads(out[out.index("sweep: trial summary") + 21 : out.index("session runs:")])[
            "runs_used"
        ]
        == 29
    )


def test_trial_summary_counts_candidates_never_reached(tmp_path, monkeypatch):
    paths = sweep_setup(tmp_path, monkeypatch, ["pass"] * 5)
    assert score.run_sweep(tmp_path, paths, "2.22.0", 0, "s", max_runs=10) == 0
    summary = score.trial_summary(ledger.load(tmp_path / "runs" / "ledger.jsonl"), RULES_BY_CASE)
    assert (summary["reached"], summary["never_reached"], summary["runs_used"]) == (3, 2, 9)
    assert summary["cases_reproduced"] == 0
    with pytest.raises(ValueError, match="one trial line"):
        score.trial_summary([], RULES_BY_CASE)


def test_a_rule_cut_off_before_all_its_controls_ran(tmp_path, candidates):
    a = candidates["s2-solo-c2-short-together"]
    q = queues(
        a,
        many(("fail-no-oversell-and-reserved", 13)),
        pr_16961=many(("fail-no-oversell", 10)),
        pr_17420=many(("pass", 10)),
    )
    attempts, stop, _, _ = sweep_of(tmp_path, [(a, q)], budget=Budget(session_runs=23))
    entry = attempts[0].entry
    assert entry["stop_reason"].startswith("session runs cap reached")
    assert entry["reproduced"]["rules"] == {
        "no_oversell": score.CUT_OFF,
        "reserved_matches_reservations": score.CUT_OFF,
    }


def test_the_summary_relabels_cut_off_lines_written_before_the_label(tmp_path):
    entry = {
        "stop_reason": "session runs cap reached: used 290 of 300, asked for 10 more",
        "controls": [],
        "reproduced": {"cases": {}, "rules": {"no_oversell": score.NOT_ISOLATED}},
    }
    assert score.rule_outcome(entry, "no_oversell", RULES_BY_CASE) == score.CUT_OFF
    ran = dict(entry, controls=[{"cases": [LINES]}])
    assert score.rule_outcome(ran, "no_oversell", RULES_BY_CASE) == score.CUT_OFF
    ran = dict(entry, controls=[{"cases": [LINES]}, {"cases": [LAST_UNIT]}])
    assert score.rule_outcome(ran, "no_oversell", RULES_BY_CASE) == score.NOT_ISOLATED
    not_capped = dict(entry, stop_reason=None)
    assert score.rule_outcome(not_capped, "no_oversell", RULES_BY_CASE) == score.NOT_ISOLATED


BASELINES = ROOT / "benchmark" / "baselines" / "2004ed5"


def test_baseline_summaries_from_the_committed_ledgers():
    got = {}
    for d in sorted(BASELINES.iterdir()):
        records = ledger.load(d / "ledger.jsonl")
        s = score.trial_summary(records, RULES_BY_CASE)
        finals = [r for r in records if r.get("kind") == "final"]
        assert s["runs_used"] == sum(r["oversold_runs"] for r in finals)
        got[d.name] = (
            s["runs_used"],
            s["reached"],
            s["cases_reproduced"],
            s["violations"],
            s["cause_not_isolated"],
            s["cut_off_by_run_cap"],
        )
    assert got == {
        "grid-seed-1": (298, 16, 3, 10, 0, 0),
        "grid-seed-2": (293, 21, 3, 10, 0, 1),
        "grid-seed-3": (297, 19, 3, 11, 0, 1),
        "grid-seed-4": (297, 19, 3, 10, 0, 1),
        "grid-seed-5": (300, 20, 3, 10, 0, 1),
        "grid-seed-6": (300, 20, 3, 9, 0, 0),
        "grid-seed-7": (297, 19, 3, 10, 0, 1),
        "grid-seed-8": (295, 25, 3, 10, 0, 1),
        "grid-seed-9": (300, 20, 3, 10, 0, 1),
        "grid-seed-10": (300, 20, 3, 9, 0, 0),
        "random-seed-1": (299, 51, 2, 7, 0, 1),
        "random-seed-2": (296, 48, 3, 7, 0, 1),
        "random-seed-3": (291, 59, 2, 6, 0, 1),
        "random-seed-4": (300, 40, 3, 7, 1, 0),
        "random-seed-5": (300, 70, 3, 5, 0, 1),
        "random-seed-6": (300, 62, 3, 5, 0, 0),
        "random-seed-7": (300, 44, 3, 7, 0, 0),
        "random-seed-8": (291, 67, 2, 6, 0, 1),
        "random-seed-9": (298, 54, 2, 7, 0, 0),
        "random-seed-10": (300, 52, 3, 6, 1, 0),
    }


def missing_orders_pass_with_unknown_completion() -> dict:
    h = hist("pass")
    h["verdicts"] = [
        *(v for v in h["verdicts"] if v["check"] != "no_missing_orders"),
        {"check": "no_missing_orders", "version": 1, "result": "pass", "reason": "cart skipped"},
    ]
    h["operations"] = unknown_call("pass")["operations"]
    return h


def test_an_unknown_completion_never_counts_as_a_no_missing_orders_pass(tmp_path, candidates):
    h = missing_orders_pass_with_unknown_completion()
    assert all(v["result"] == "pass" for v in h["verdicts"])
    c = score.counts([h])
    assert c["no_missing_orders"] == {"fail": 0, "pass": 0, "inconclusive": 1}
    assert all(row["pass"] == 0 for row in c.values())
    assert score.inconclusive_runs([h]) == 1
    path = candidates["s2-solo-c2-short-together"]
    q = queues(path, [missing_orders_pass_with_unknown_completion() for _ in range(10)])
    entry, stop, _, _ = attempt(tmp_path, path, q)
    assert entry["violation"]["result"] == "inconclusive"
    assert sum(entry["inconclusive"].values()) == entry["violation"]["runs"] == 10
