import pytest

from shortfall.budget import (
    ATTEMPT,
    DEFAULT_ATTEMPT_RUNS,
    DEFAULT_DOLLARS,
    DEFAULT_SESSION_RUNS,
    DOLLARS,
    SESSION,
    Budget,
    CapReached,
    from_flags,
)
from shortfall.sweep import parse_args


def test_defaults():
    b = Budget()
    assert (b.session_runs, b.attempt_runs, b.dollars) == (600, 25, 0.0)
    assert (DEFAULT_SESSION_RUNS, DEFAULT_ATTEMPT_RUNS, DEFAULT_DOLLARS) == (600, 25, 0.0)


def test_session_cap_stops_and_never_goes_over():
    b = Budget(session_runs=10, attempt_runs=100)
    b.start_attempt()
    for _ in range(3):
        b.charge_runs(3)
    with pytest.raises(CapReached) as err:
        b.charge_runs(3)
    assert err.value.cap == SESSION
    assert b.session_used == 9
    b.charge_runs(1)
    assert b.session_used == 10
    with pytest.raises(CapReached):
        b.charge_runs(1)
    assert b.session_used == 10
    assert b.session_left() == 0


def test_attempt_cap_stops_and_resets():
    b = Budget(session_runs=600, attempt_runs=25)
    b.start_attempt()
    b.charge_runs(3)
    b.charge_runs(10)
    b.charge_runs(10)
    with pytest.raises(CapReached) as err:
        b.charge_runs(3)
    assert err.value.cap == ATTEMPT
    assert b.attempt_used == 23
    b.start_attempt()
    b.charge_runs(3)
    assert b.attempt_used == 3
    assert b.session_used == 26
    assert b.attempts == 2


def test_dollar_cap_defaults_to_zero():
    b = Budget()
    b.charge_dollars(0)
    with pytest.raises(CapReached) as err:
        b.charge_dollars(0.01)
    assert err.value.cap == DOLLARS
    assert b.dollars_used == 0


def test_raised_dollar_cap_still_stops():
    b = from_flags(raise_dollar_cap=1.0)
    b.charge_dollars(0.6)
    with pytest.raises(CapReached):
        b.charge_dollars(0.5)
    assert b.dollars_used == pytest.approx(0.6)


def test_max_runs_overrides_session_cap_only():
    b = from_flags(max_runs=50)
    assert b.session_runs == 50
    assert b.attempt_runs == 25
    assert b.dollars == 0


def test_flags():
    args = parse_args(["--max-runs", "40"])
    assert args.max_runs == 40
    assert args.raise_dollar_cap is None
    with pytest.raises(SystemExit):
        parse_args(["--max-runs", "0"])
    with pytest.raises(SystemExit):
        parse_args(["--raise-dollar-cap", "-1"])
    with pytest.raises(SystemExit):
        parse_args(["--version", "latest"])


@pytest.mark.parametrize(
    "kwargs",
    [{"session_runs": -1}, {"attempt_runs": 2.5}, {"dollars": -0.5}],
)
def test_bad_caps(kwargs):
    with pytest.raises(ValueError):
        Budget(**kwargs)


def test_bad_charges():
    b = Budget()
    with pytest.raises(ValueError):
        b.charge_runs(0)
    with pytest.raises(ValueError):
        b.charge_dollars(-1)


def test_describe_reports_each_cap():
    b = Budget(session_runs=10)
    b.start_attempt()
    b.charge_runs(3)
    text = b.describe()
    assert "session runs: used 3 of 10" in text
    assert "attempt runs: last attempt used 3 of 25" in text
    assert "dollars: used 0.00 of 0.00" in text
