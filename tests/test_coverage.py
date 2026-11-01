from pathlib import Path

import pytest
import yaml

from shortfall.coverage import ISSUE_16502, ISSUE_16825, ISSUE_17032, covering_issues
from shortfall.score import shape

CASES = Path(__file__).resolve().parent.parent / "benchmark" / "cases"
BASE = {"servers": 2, "carts": 2, "item_on_several_lines": False, "release": "together"}
MULTI = {**BASE, "item_on_several_lines": True}


@pytest.mark.parametrize("locking", [None, "in-memory"])
def test_in_memory_locking_keeps_17032(locking):
    s = dict(BASE) if locking is None else {**BASE, "locking": locking}
    assert covering_issues(s, "no_oversell") == (ISSUE_17032,)
    assert covering_issues(s, "reserved_matches_reservations") == (ISSUE_17032,)
    m = {**s, "item_on_several_lines": True}
    assert covering_issues(m, "no_oversell") == (ISSUE_17032, ISSUE_16502)
    assert covering_issues({**m, "servers": 1}, "no_oversell") == (ISSUE_16502, ISSUE_17032)


def test_redis_locking_takes_17032_out_of_the_map():
    redis = {**BASE, "locking": "redis"}
    assert covering_issues(redis, "no_oversell") == ()
    assert covering_issues(redis, "reserved_matches_reservations") == ()
    assert covering_issues({**MULTI, "locking": "redis"}, "no_oversell") == (ISSUE_16502,)
    one = {**MULTI, "servers": 1, "locking": "redis"}
    assert covering_issues(one, "no_oversell") == (ISSUE_16502,)
    assert covering_issues(redis, "no_orphaned_orders") == (ISSUE_16825,)
    assert covering_issues(redis, "one_order_per_cart") == ()


@pytest.mark.parametrize("case", ["medusa-17032-last-unit", "medusa-17032-counter"])
def test_no_issue_covers_a_stock_failure_in_a_redis_control(case):
    s = shape(yaml.safe_load((CASES / case / "redis-control.yaml").read_text(encoding="utf-8")))
    for rule in ("no_oversell", "reserved_matches_reservations", "one_order_per_cart"):
        assert covering_issues(s, rule) == ()
    ref = shape(yaml.safe_load((CASES / case / "reference.yaml").read_text(encoding="utf-8")))
    assert covering_issues(ref, "no_oversell") == (ISSUE_17032,)
