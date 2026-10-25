import shutil
from pathlib import Path

import pytest

from shortfall import ledger, score
from shortfall.budget import DOLLARS, TOTAL_DOLLARS, CapReached, from_flags
from shortfall.spend import Meter, Usage

ROOT = Path(__file__).resolve().parent.parent
MODEL = "test-model"


def meter(path: Path, budget, n: int) -> Meter:
    m = Meter(path, budget, f"s-{n:03d}")
    budget.start_attempt()
    m.start(
        {
            "source": "sweep",
            "seed": 0,
            "scenario": f"runs/sweep/s/grid-{n:03d}.yaml",
            "scenario_sha256": "0" * 64,
            "medusa_version": "2.21.2",
            "medusa_image_id": "sha256:" + "1" * 64,
            "oversold_commit": "a" * 40,
            "rerun_of": None,
        }
    )
    return m


def call_costing(dollars: float, calls: list | None = None):
    def call():
        if calls is not None:
            calls.append(dollars)
        return "reply", Usage(MODEL, 1000, 200, dollars)

    return call


def session(path: Path, raise_dollar_cap: float):
    return from_flags(
        raise_dollar_cap=raise_dollar_cap, dollars_before=ledger.spent(ledger.load(path))["dollars"]
    )


def test_a_paid_call_is_in_the_ledger_before_and_after_it_runs(tmp_path):
    path = tmp_path / "ledger.jsonl"
    seen = []

    def call():
        seen.append([r["state"] for r in ledger.load(path) if r["kind"] == "spend"])
        return "reply", Usage(MODEL, 1200, 300, 0.04)

    m = meter(path, from_flags(raise_dollar_cap=1.0), 1)
    assert m.paid_call(MODEL, 0.1, call) == "reply"
    assert seen == [["reserved"]]
    spends = [r for r in ledger.load(path) if r["kind"] == "spend"]
    assert [(r["state"], r["dollars"]) for r in spends] == [("reserved", 0.1), ("settled", 0.04)]
    assert (spends[1]["model"], spends[1]["input_tokens"], spends[1]["output_tokens"]) == (
        MODEL,
        1200,
        300,
    )
    assert ledger.spent(ledger.load(path))["dollars"] == pytest.approx(0.04)


def test_no_paid_call_without_raising_the_session_cap(tmp_path):
    path = tmp_path / "ledger.jsonl"
    calls = []
    m = meter(path, from_flags(), 1)
    with pytest.raises(CapReached) as err:
        m.paid_call(MODEL, 0.01, call_costing(0.01, calls))
    assert err.value.cap == DOLLARS
    assert calls == []
    assert [r["kind"] for r in ledger.load(path)] == ["started"]


def test_a_new_session_cannot_go_past_the_total_cap(tmp_path):
    path = tmp_path / "ledger.jsonl"
    first = meter(path, session(path, 20.0), 1)
    for _ in range(3):
        first.paid_call(MODEL, 6.5, call_costing(6.5))
    assert ledger.spent(ledger.load(path))["dollars"] == pytest.approx(19.5)

    budget = session(path, 10.0)
    assert budget.dollars_before == pytest.approx(19.5)
    second = meter(path, budget, 2)
    calls = []
    lines = len(ledger.load(path))
    with pytest.raises(CapReached) as err:
        second.paid_call(MODEL, 0.6, call_costing(0.1, calls))
    assert err.value.cap == TOTAL_DOLLARS
    assert calls == []
    assert len(ledger.load(path)) == lines
    second.paid_call(MODEL, 0.5, call_costing(0.5))
    assert ledger.spent(ledger.load(path))["dollars"] == pytest.approx(20.0)

    third = meter(path, session(path, 10.0), 3)
    with pytest.raises(CapReached) as err:
        third.paid_call(MODEL, 0.01, call_costing(0.01, calls))
    assert err.value.cap == TOTAL_DOLLARS
    assert calls == []


def test_a_killed_paid_call_counts_its_reservation(tmp_path):
    path = tmp_path / "ledger.jsonl"

    def dies():
        raise KeyboardInterrupt

    m = meter(path, from_flags(raise_dollar_cap=5.0), 1)
    with pytest.raises(KeyboardInterrupt):
        m.paid_call(MODEL, 2.0, dies)
    records = ledger.load(path)
    [a] = ledger.attempts(records)
    assert a["verdict"] == ledger.INTERRUPTED
    assert a["dollars"] == pytest.approx(2.0)
    totals = ledger.spent(records)
    assert totals["dollars"] == pytest.approx(2.0)
    assert totals["unsettled_calls"] == 1
    assert session(path, 20.0).dollars_before == pytest.approx(2.0)


def test_a_call_above_its_reservation_is_recorded_then_refused(tmp_path):
    path = tmp_path / "ledger.jsonl"
    m = meter(path, from_flags(raise_dollar_cap=5.0), 1)
    with pytest.raises(RuntimeError, match="above its reservation"):
        m.paid_call(MODEL, 0.1, call_costing(0.3))
    assert ledger.spent(ledger.load(path))["dollars"] == pytest.approx(0.3)


def test_each_session_starts_from_the_ledger_total(tmp_path, monkeypatch, capsys):
    shutil.copytree(
        ROOT / "benchmark" / "cases",
        tmp_path / "benchmark" / "cases",
        ignore=shutil.ignore_patterns("results"),
    )
    path = score.ledger_path_for(tmp_path)
    m = meter(path, from_flags(raise_dollar_cap=20.0), 1)
    m.paid_call(MODEL, 19.0, call_costing(19.0))

    class Fake:
        def __init__(self, root):
            self.pin = "a" * 40

        def image(self, version):
            return "sha256:" + "1" * 64, "none"

    monkeypatch.setattr(score, "OversoldRunner", Fake)
    budget, *_ = score._start(tmp_path, "2.21.2", None, 5.0)
    assert budget.dollars_before == pytest.approx(19.0)
    assert "19.00 of 20.00 dollars" in capsys.readouterr().out
    with pytest.raises(CapReached) as err:
        budget.reserve_dollars(1.5)
    assert err.value.cap == TOTAL_DOLLARS
