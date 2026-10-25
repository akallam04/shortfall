import json
import os

import pytest

from shortfall import ledger

STAMP = "20261025T000000Z"


def entry(n: int, verdict: str = "no match", case: str | None = None, runs: int = 3) -> dict:
    return {
        "kind": "final",
        "attempt_id": f"{STAMP}-{n:03d}",
        "source": "sweep",
        "seed": 0,
        "scenario": f"runs/sweep/{STAMP}/grid-{n:03d}.yaml",
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
        "dollars": 0,
        "oversold_commit": "a" * 40,
        "medusa_image_id": "sha256:" + "b" * 64,
        "medusa_image_digest": "none",
        "run_folders": ["runs/x"],
        "stop_reason": None,
        "setup_error": None,
        "manual_check": [],
        "rerun_of": None,
        "timestamp": "2026-10-25T00:00:00+00:00",
    }


def legacy(n: int, verdict: str = "no match", runs: int = 3) -> dict:
    e = entry(n, verdict, runs=runs)
    for key in ("kind", "dollars", "manual_check", "setup_error"):
        e.pop(key)
    return e


def started(n: int) -> dict:
    return {
        "kind": "started",
        "attempt_id": f"{STAMP}-{n:03d}",
        "source": "sweep",
        "seed": 0,
        "scenario": f"runs/sweep/{STAMP}/grid-{n:03d}.yaml",
        "scenario_sha256": "0" * 64,
        "medusa_version": "2.21.2",
        "medusa_image_id": "sha256:" + "b" * 64,
        "oversold_commit": "a" * 40,
        "rerun_of": None,
        "timestamp": "2026-10-25T00:00:00+00:00",
    }


def runs_spend(n: int, k: int, runs: int, set_name: str = "screen") -> dict:
    return {
        "kind": "spend",
        "attempt_id": f"{STAMP}-{n:03d}",
        "spend_id": f"{STAMP}-{n:03d}-s{k:02d}",
        "item": "oversold_runs",
        "state": "charged",
        "set": set_name,
        "oversold_runs": runs,
        "model": None,
        "input_tokens": None,
        "output_tokens": None,
        "dollars": 0,
        "timestamp": "2026-10-25T00:00:00+00:00",
    }


def paid(n: int, k: int, state: str, dollars: float, tokens=(None, None)) -> dict:
    return {
        "kind": "spend",
        "attempt_id": f"{STAMP}-{n:03d}",
        "spend_id": f"{STAMP}-{n:03d}-s{k:02d}",
        "item": "paid_call",
        "state": state,
        "set": None,
        "oversold_runs": None,
        "model": "test-model",
        "input_tokens": tokens[0],
        "output_tokens": tokens[1],
        "dollars": dollars,
        "timestamp": "2026-10-25T00:00:00+00:00",
    }


def write(path, records):
    for r in records:
        ledger.append(path, r)


def test_round_trip(tmp_path):
    path = tmp_path / "runs" / "ledger.jsonl"
    written = [
        entry(1),
        entry(2, "match", "medusa-17032-last-unit", 23),
        entry(3, "reproduction only", "medusa-16502-lines", 13),
    ]
    write(path, written)
    loaded = ledger.load(path)
    assert loaded == written
    assert list(loaded[0]) == list(ledger.FINAL_FIELDS)
    assert ledger.find(loaded, written[1]["attempt_id"])["verdict"] == "match"
    with pytest.raises(KeyError):
        ledger.find(loaded, "nope")


def test_legacy_lines_still_load_and_count(tmp_path):
    path = tmp_path / "ledger.jsonl"
    old = [legacy(1, runs=3), legacy(2, "match", runs=23)]
    path.write_text("".join(json.dumps(e) + "\n" for e in old), encoding="utf-8")
    records = ledger.load(path)
    assert records == old
    assert ledger.spent(records) == {"oversold_runs": 26, "dollars": 0.0, "unsettled_calls": 0}
    assert ledger.summary(records)["by_verdict"]["match"] == 1


def test_appending_needs_a_kind(tmp_path):
    with pytest.raises(ValueError, match="kind is required"):
        ledger.append(tmp_path / "ledger.jsonl", legacy(1))


def test_started_without_final_is_interrupted_with_its_charges(tmp_path):
    path = tmp_path / "ledger.jsonl"
    write(
        path,
        [
            started(1),
            runs_spend(1, 1, 1),
            runs_spend(1, 2, 2),
            runs_spend(1, 3, 10, "score"),
        ],
    )
    records = ledger.load(path)
    [a] = ledger.attempts(records)
    assert a["verdict"] == ledger.INTERRUPTED
    assert a["oversold_runs"] == 13
    s = ledger.summary(records)
    assert s["by_verdict"][ledger.INTERRUPTED] == 1
    assert s["oversold_runs"] == 13
    with pytest.raises(KeyError):
        ledger.find(records, f"{STAMP}-001")


def test_finished_attempt_counts_its_spend_lines_once(tmp_path):
    path = tmp_path / "ledger.jsonl"
    write(
        path,
        [
            started(1),
            runs_spend(1, 1, 1),
            runs_spend(1, 2, 2),
            entry(1, runs=3),
            started(2),
            runs_spend(2, 1, 1),
        ],
    )
    records = ledger.load(path)
    assert [a["verdict"] for a in ledger.attempts(records)] == ["no match", ledger.INTERRUPTED]
    assert ledger.spent(records)["oversold_runs"] == 4


def test_paid_calls_count_their_reservation_until_settled(tmp_path):
    path = tmp_path / "ledger.jsonl"
    write(
        path,
        [
            started(1),
            paid(1, 1, "reserved", 0.75),
            paid(1, 1, "settled", 0.12, (1000, 200)),
            paid(1, 2, "reserved", 0.5),
        ],
    )
    records = ledger.load(path)
    totals = ledger.spent(records)
    assert totals["dollars"] == pytest.approx(0.62)
    assert totals["unsettled_calls"] == 1
    assert ledger.attempts(records)[0]["dollars"] == pytest.approx(0.62)


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
        entry(7, "unpreparable", runs=1),
    ]
    s = ledger.summary(entries)
    assert s["attempts"] == 7
    assert sum(s["by_verdict"].values()) == 7
    assert s["by_verdict"] == {
        "match": 2,
        "no match": 2,
        "reproduction only": 1,
        "inconclusive": 1,
        "unpreparable": 1,
        "interrupted": 0,
    }
    assert sum(sum(v.values()) for v in s["by_case"].values()) == 7
    assert s["by_case"]["none"] == {"inconclusive": 1, "no match": 2, "unpreparable": 1}
    assert s["by_case"]["medusa-17032-last-unit"] == {"match": 1}
    assert s["oversold_runs"] == 3 + 3 + 23 + 23 + 13 + 3 + 1
    assert s["dollars"] == 0
    assert s["wall_seconds"] == 87.5


@pytest.mark.parametrize(
    "record,change,message",
    [
        (entry(1), lambda e: e.update(scenario="/tmp/grid-001.yaml"), "local path"),
        (
            entry(1),
            lambda e: e["shape"].update(note=os.path.expanduser("~") + "/x"),
            "local path",
        ),
        (
            entry(1),
            lambda e: e.update(
                stop_reason="error: " + os.path.dirname(os.path.expanduser("~")) + "/someone/x"
            ),
            "local path",
        ),
        (entry(1), lambda e: e.update(extra=1), "unknown field extra"),
        (entry(1), lambda e: e.update(verdict="maybe"), "verdict"),
        (entry(1), lambda e: e.update(verdict="interrupted"), "verdict"),
        (entry(1), lambda e: e.update(source="agent"), "source"),
        (entry(1), lambda e: e.pop("timestamp"), "timestamp is required"),
        (entry(1), lambda e: e.pop("dollars"), "dollars is required"),
        (entry(1), lambda e: e.update(kind="other"), "kind must be one of"),
        (started(1), lambda e: e.pop("scenario"), "scenario is required"),
        (runs_spend(1, 1, 3), lambda e: e.update(oversold_runs=0), "oversold_runs must be above"),
        (runs_spend(1, 1, 3), lambda e: e.update(dollars=1), "costs 0 dollars"),
        (runs_spend(1, 1, 3), lambda e: e.update(item="coffee"), "item must be one of"),
        (paid(1, 1, "reserved", 0.5), lambda e: e.update(model=""), "needs a model"),
        (paid(1, 1, "reserved", 0.5), lambda e: e.update(dollars=-1), "dollars must be 0"),
        (paid(1, 1, "settled", 0.5), lambda e: None, "needs input_tokens"),
        (paid(1, 1, "reserved", 0.5, (1, 1)), lambda e: None, "no tokens yet"),
    ],
)
def test_bad_records_refused(tmp_path, record, change, message):
    change(record)
    path = tmp_path / "ledger.jsonl"
    with pytest.raises(ValueError, match=message):
        ledger.append(path, record)
    assert not path.exists()
