import math

import pytest

from shortfall import stats


def test_fisher_exact_two_sided_reference_values():
    assert stats.fisher_exact(3, 1, 1, 3) == pytest.approx(0.4857142857)
    assert stats.fisher_exact(3, 7, 10, 0) == pytest.approx(0.0030959752)
    assert stats.fisher_exact(7, 3, 10, 0) == pytest.approx(0.2105263158)
    assert stats.fisher_exact(10, 0, 10, 0) == 1.0


def test_fisher_exact_is_symmetric():
    assert stats.fisher_exact(2, 8, 7, 3) == pytest.approx(stats.fisher_exact(7, 3, 2, 8))


def test_holm_keeps_order_and_caps_at_one():
    assert stats.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert stats.holm([0.5, 0.9]) == [1.0, 1.0]


def test_ranks_share_ties():
    assert stats.ranks([33, 33, 58.5, 301, 301]) == [1.5, 1.5, 3.0, 4.5, 4.5]


def test_mann_whitney_normal_approximation():
    p = stats.mann_whitney([1, 2, 3, 4, 5], [6, 7, 8, 9, 10])
    z = (25 - 12.5 - 0.5) / math.sqrt(25 / 12 * 11)
    assert p == pytest.approx(math.erfc(z / math.sqrt(2)))
    assert p == pytest.approx(0.0122, abs=0.0001)


def test_mann_whitney_is_symmetric_and_handles_identical_samples():
    x, y = [33, 33, 301, 43], [58, 33, 121, 209]
    assert stats.mann_whitney(x, y) == pytest.approx(stats.mann_whitney(y, x))
    assert stats.mann_whitney([33, 33], [33, 33]) == 1.0
