import os

import pytest

from shortfall import ledger


def entry(n: int, verdict: str = "no match", case: str | None = None, runs: int = 3) -> dict:
    return {
        "attempt_id": f"20261025T000000Z-{n:03d}",
        "source": "sweep",
        "seed": 0,
        "scenario": f"runs/sweep/20261025T000000Z/grid-{n:03d}.yaml",
        "scenario_sha256": "0" * 64,
        "case": case,
        "cases": [case] if case else [],
        "medusa_version": "2.21.2",
        "carts": 2,
        "servers": 2,
        "shape": {"servers": 2, "carts": 2, "groups": [], "stock": {"SOLO": 1}},
        "screen_runs": 3,
        "score_runs": 10 if runs > 3 else 0,
        "control_runs": 10 if runs > 13 else 0,
        "candidate_fails": {"screen": {"no_oversell": 1}, "score": None},
        "control_fails": None,
        "inconclusive": {"screen": 0, "score": 0, "control": 0},
        "rules_failed": [],
        "verdict": verdict,
        "wall_seconds": 12.5,
        "oversold_runs": runs,
        "oversold_commit": "a" * 40,
        "medusa_image_id": "sha256:" + "b" * 64,
        "medusa_image_digest": "none",
        "run_folders": ["runs/x"],
        "stop_reason": None,
        "rerun_of": None,
        "timestamp": "2026-10-25T00:00:00+00:00",
    }


def test_round_trip(tmp_path):
    path = tmp_path / "runs" / "ledger.jsonl"
    written = [
        entry(1),
        entry(2, "match", "medusa-17032-last-unit", 23),
        entry(3, "reproduction only", "medusa-16502-lines", 13),
    ]
    for e in written:
        ledger.append(path, e)
    loaded = ledger.load(path)
    assert loaded == written
    assert list(loaded[0]) == list(ledger.FIELDS)
    assert ledger.find(loaded, written[1]["attempt_id"])["verdict"] == "match"
    with pytest.raises(KeyError):
        ledger.find(loaded, "nope")


def test_missing_ledger_loads_empty(tmp_path):
    assert ledger.load(tmp_path / "ledger.jsonl") == []


def test_summary_adds_up():
    entries = [
        entry(1),
        entry(2),
        entry(3, "match", "medusa-17032-last-unit", 23),
        entry(4, "match", "medusa-17032-counter", 23),
        entry(5, "reproduction only", "medusa-16502-lines", 13),
        entry(6, "inconclusive"),
    ]
    s = ledger.summary(entries)
    assert s["attempts"] == 6
    assert sum(s["by_verdict"].values()) == 6
    assert s["by_verdict"] == {
        "match": 2,
        "no match": 2,
        "reproduction only": 1,
        "inconclusive": 1,
    }
    assert sum(sum(v.values()) for v in s["by_case"].values()) == 6
    assert s["by_case"]["none"] == {"inconclusive": 1, "no match": 2}
    assert s["by_case"]["medusa-17032-last-unit"] == {"match": 1}
    assert s["oversold_runs"] == 3 + 3 + 23 + 23 + 13 + 3
    assert s["wall_seconds"] == 75.0


@pytest.mark.parametrize(
    "change,message",
    [
        (lambda e: e.update(scenario="/tmp/grid-001.yaml"), "local path"),
        (lambda e: e["shape"].update(note=os.path.expanduser("~") + "/x"), "local path"),
        (
            lambda e: e.update(
                stop_reason="error: " + os.path.dirname(os.path.expanduser("~")) + "/someone/x"
            ),
            "local path",
        ),
        (lambda e: e.update(extra=1), "unknown field extra"),
        (lambda e: e.update(verdict="maybe"), "verdict"),
        (lambda e: e.update(source="agent"), "source"),
        (lambda e: e.pop("timestamp"), "timestamp is required"),
    ],
)
def test_bad_entries_refused(tmp_path, change, message):
    e = entry(1)
    change(e)
    path = tmp_path / "ledger.jsonl"
    with pytest.raises(ValueError, match=message):
        ledger.append(path, e)
    assert not path.exists()
