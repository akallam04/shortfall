import json
import shutil
from pathlib import Path

import pytest

from shortfall import ledger, score, sweep
from shortfall.budget import Budget

ROOT = Path(__file__).resolve().parent.parent
HISTORIES = Path(__file__).resolve().parent / "data" / "histories"
CASES = score.case_map(ROOT / "benchmark" / "cases")
IMAGE = "sha256:" + "1" * 64
PIN = "a18d5c9f3892dbca86effa0766e975985f8324bd"


def hist(name: str) -> dict:
    return json.loads((HISTORIES / f"{name}.json").read_text(encoding="utf-8"))


def many(*parts: tuple[str, int]) -> list[dict]:
    out = []
    for name, n in parts:
        out += [hist(name) for _ in range(n)]
    return out


class FixtureRunner:
    def __init__(self, sets: dict[tuple[str, int], list[dict]]):
        self.sets = sets
        self.calls: list[tuple[str, int]] = []

    def run(self, scenario: Path, runs: int, version: str) -> score.RunSet:
        key = (scenario.stem, runs)
        self.calls.append(key)
        histories = self.sets[key]
        assert len(histories) == runs
        return score.RunSet(folder=f"runs/fixture-{scenario.stem}-{runs}", histories=histories)


@pytest.fixture
def candidates(tmp_path):
    paths = sweep.write(sweep.grid(0), tmp_path / "runs" / "sweep" / "s")
    return {p.stem: p for p in paths}


def attempt(tmp_path, path, sets, budget=None):
    runner = FixtureRunner(sets)
    budget = budget or Budget()
    meta = {"attempt_id": "s-001", "source": "sweep", "seed": 0, "rerun_of": None}
    entry, stop = score.score_candidate(
        tmp_path, path, "2.21.2", runner, budget, CASES, IMAGE, "none", PIN, meta
    )
    ledger.validate(entry)
    return entry, stop, runner, budget


def test_case_map_from_rule_and_server_count():
    assert CASES == {
        ("no_oversell", 2): "medusa-17032-last-unit",
        ("reserved_matches_reservations", 2): "medusa-17032-counter",
        ("no_oversell", 1): "medusa-16502-lines",
    }


def test_one_of_ten_on_candidate_and_clean_control_is_a_match(tmp_path, candidates):
    name = "grid-002-s2-solo-c2-short-together"
    entry, stop, runner, budget = attempt(
        tmp_path,
        candidates[name],
        {
            (name, 3): many(("fail-no-oversell-and-reserved", 1), ("pass", 2)),
            (name, 10): many(("fail-no-oversell-and-reserved", 1), ("pass", 9)),
            (f"{name}-control", 10): many(("pass", 10)),
        },
    )
    assert stop is None
    assert entry["verdict"] == "match"
    assert entry["case"] == "medusa-17032-last-unit"
    assert entry["cases"] == ["medusa-17032-last-unit", "medusa-17032-counter"]
    assert entry["candidate_fails"]["score"]["no_oversell"] == 1
    assert entry["control_fails"] == dict.fromkeys(entry["control_fails"], 0)
    assert entry["oversold_runs"] == 23 == budget.session_used
    assert runner.calls == [(name, 3), (name, 10), (f"{name}-control", 10)]
    assert (candidates[name].parent / f"{name}-control.yaml").exists()


def test_reserved_only_matches_the_counter_case(tmp_path, candidates):
    name = "grid-012-s2-piece-c10-ample-together"
    entry, stop, _, _ = attempt(
        tmp_path,
        candidates[name],
        {
            (name, 3): many(("fail-reserved", 3)),
            (name, 10): many(("fail-reserved", 10)),
            (f"{name}-control", 10): many(("pass", 10)),
        },
    )
    assert entry["verdict"] == "match"
    assert entry["case"] == "medusa-17032-counter"
    assert entry["rules_failed"] == ["reserved_matches_reservations"]


def test_a_failure_on_the_control_is_not_a_match(tmp_path, candidates):
    name = "grid-014-s2-piece-twopack-c2-short-together"
    entry, stop, _, _ = attempt(
        tmp_path,
        candidates[name],
        {
            (name, 3): many(("fail-no-oversell", 3)),
            (name, 10): many(("fail-no-oversell", 10)),
            (f"{name}-control", 10): many(("fail-no-oversell", 1), ("pass", 9)),
        },
    )
    assert stop is None
    assert entry["verdict"] == "no match"
    assert entry["case"] is None
    assert entry["control_fails"]["no_oversell"] == 1


def test_clean_screen_is_no_match_and_stops_at_three_runs(tmp_path, candidates):
    name = "grid-003-s2-solo-c2-ample-together"
    entry, stop, runner, budget = attempt(
        tmp_path, candidates[name], {(name, 3): many(("pass", 3))}
    )
    assert entry["verdict"] == "no match"
    assert entry["score_runs"] == 0 and entry["control_runs"] == 0
    assert budget.session_used == 3
    assert runner.calls == [(name, 3)]


def test_screen_failure_that_does_not_repeat_is_no_match(tmp_path, candidates):
    name = "grid-002-s2-solo-c2-short-together"
    entry, _, runner, _ = attempt(
        tmp_path,
        candidates[name],
        {
            (name, 3): many(("fail-no-oversell-and-reserved", 1), ("pass", 2)),
            (name, 10): many(("pass", 10)),
        },
    )
    assert entry["verdict"] == "no match"
    assert entry["rules_failed"] == ["no_oversell", "reserved_matches_reservations"]
    assert len(runner.calls) == 2


def test_one_server_failure_is_reproduction_only(tmp_path, candidates):
    name = "grid-032-s1-piece-twopack-c2-short-together"
    entry, stop, runner, budget = attempt(
        tmp_path,
        candidates[name],
        {(name, 3): many(("fail-no-oversell", 3)), (name, 10): many(("fail-no-oversell", 10))},
    )
    assert stop is None
    assert entry["verdict"] == "reproduction only"
    assert entry["case"] == "medusa-16502-lines"
    assert entry["control_runs"] == 0 and entry["control_fails"] is None
    assert budget.session_used == 13
    assert not (candidates[name].parent / f"{name}-control.yaml").exists()


def test_partly_inconclusive_screen_is_inconclusive(tmp_path, candidates):
    name = "grid-003-s2-solo-c2-ample-together"
    entry, stop, _, budget = attempt(
        tmp_path, candidates[name], {(name, 3): many(("inconclusive", 1), ("pass", 2))}
    )
    assert entry["verdict"] == "inconclusive"
    assert entry["inconclusive"]["screen"] == 1
    assert stop is None
    assert entry["oversold_runs"] == 3 == budget.session_used


def test_all_inconclusive_set_is_recorded_without_stopping(tmp_path, candidates):
    name = "grid-003-s2-solo-c2-ample-together"
    entry, stop, _, _ = attempt(tmp_path, candidates[name], {(name, 3): many(("inconclusive", 3))})
    assert entry["verdict"] == "inconclusive"
    assert stop is None
    assert entry["oversold_runs"] == 3
    assert score.only_inconclusive(entry)


def test_uncovered_rule_stops_the_sweep(tmp_path, candidates):
    name = "grid-002-s2-solo-c2-short-together"
    entry, stop, runner, _ = attempt(
        tmp_path,
        candidates[name],
        {(name, 3): many(("constructed-fail-one-order", 1), ("pass", 2))},
    )
    assert stop and stop.startswith("uncovered failure: one_order_per_cart")
    assert entry["verdict"] == "inconclusive"
    assert runner.calls == [(name, 3)]


def test_one_server_single_line_oversell_is_uncovered(tmp_path, candidates):
    name = "grid-026-s1-piece-c2-short-together"
    entry, stop, _, _ = attempt(
        tmp_path, candidates[name], {(name, 3): many(("fail-no-oversell", 1), ("pass", 2))}
    )
    assert stop and stop.startswith("uncovered failure: no_oversell")


def test_session_cap_mid_attempt_stops_cleanly(tmp_path, candidates):
    name = "grid-002-s2-solo-c2-short-together"
    budget = Budget(session_runs=10)
    entry, stop, runner, budget = attempt(
        tmp_path,
        candidates[name],
        {(name, 3): many(("fail-no-oversell-and-reserved", 3))},
        budget,
    )
    assert stop and stop.startswith("session runs cap reached")
    assert entry["verdict"] == "inconclusive"
    assert entry["screen_runs"] == 3 and entry["score_runs"] == 0
    assert budget.session_used == 3 <= budget.session_runs
    assert runner.calls == [(name, 3)]


def test_attempt_cap_ends_only_that_attempt(tmp_path, candidates):
    name = "grid-002-s2-solo-c2-short-together"
    budget = Budget(attempt_runs=20)
    entry, stop, runner, budget = attempt(
        tmp_path,
        candidates[name],
        {
            (name, 3): many(("fail-no-oversell-and-reserved", 3)),
            (name, 10): many(("fail-no-oversell-and-reserved", 10)),
        },
        budget,
    )
    assert stop is None
    assert entry["stop_reason"].startswith("attempt runs cap reached")
    assert entry["verdict"] == "inconclusive"
    assert budget.attempt_used == 13
    assert len(runner.calls) == 2


class FakeOversold:
    sets: dict = {}

    def __init__(self, root):
        self.pin = PIN
        self.runner = FixtureRunner(self.sets)

    def image(self, version):
        return IMAGE, "none"

    def run(self, scenario, runs, version):
        return self.runner.run(scenario, runs, version)


def test_run_sweep_stops_at_the_session_cap_and_writes_every_attempt(tmp_path, monkeypatch, capsys):
    shutil.copytree(
        ROOT / "benchmark" / "cases",
        tmp_path / "benchmark" / "cases",
        ignore=shutil.ignore_patterns("results"),
    )
    paths = sweep.write(sweep.grid(0)[:5], tmp_path / "runs" / "sweep" / "s")
    sets = {}
    for p in paths:
        sets[(p.stem, 3)] = many(("pass", 3))
    FakeOversold.sets = sets
    monkeypatch.setattr(score, "OversoldRunner", FakeOversold)
    code = score.run_sweep(tmp_path, paths, "2.21.2", 0, "s", max_runs=10)
    assert code == 0
    entries = ledger.load(tmp_path / "runs" / "ledger.jsonl")
    assert [e["attempt_id"] for e in entries] == ["s-001", "s-002", "s-003"]
    assert all(e["verdict"] == "no match" for e in entries)
    assert sum(e["oversold_runs"] for e in entries) == 9
    out = capsys.readouterr().out
    assert "5 candidates, 3 attempted, 3 screened, 0 scored, 2 skipped" in out
    assert "session runs: used 9 of 10" in out
    assert "dollars: used 0.00 of 0.00" in out


def sweep_setup(tmp_path, monkeypatch, outcomes):
    shutil.copytree(
        ROOT / "benchmark" / "cases",
        tmp_path / "benchmark" / "cases",
        ignore=shutil.ignore_patterns("results"),
    )
    paths = sweep.write(sweep.grid(0)[: len(outcomes)], tmp_path / "runs" / "sweep" / "s")
    FakeOversold.sets = {(p.stem, 3): many((o, 3)) for p, o in zip(paths, outcomes, strict=True)}
    monkeypatch.setattr(score, "OversoldRunner", FakeOversold)
    return paths


def test_three_inconclusive_attempts_in_a_row_stop_the_sweep(tmp_path, monkeypatch, capsys):
    outcomes = ["inconclusive", "pass", "inconclusive", "inconclusive", "inconclusive", "pass"]
    paths = sweep_setup(tmp_path, monkeypatch, outcomes)
    assert score.run_sweep(tmp_path, paths, "2.21.2", 0, "s") == 0
    entries = ledger.load(tmp_path / "runs" / "ledger.jsonl")
    assert [e["verdict"] for e in entries] == [
        "inconclusive",
        "no match",
        "inconclusive",
        "inconclusive",
        "inconclusive",
    ]
    assert "stopped: harness: 3 attempts in a row" in capsys.readouterr().out
