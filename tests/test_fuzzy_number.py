"""Tests de l'arithmétique des nombres flous triangulaires."""

from __future__ import annotations

import pytest

from maturai.domain.fuzzy_number import (
    TriangularFuzzyNumber as TFN,
)
from maturai.domain.fuzzy_number import (
    fuzzy_sum,
    fuzzy_weighted_average,
)


def test_construction_and_validation():
    assert TFN(1, 2, 3).m == 2
    with pytest.raises(ValueError):
        TFN(3, 2, 1)  # a <= m <= b violé


def test_crisp_and_width():
    c = TFN.crisp(5)
    assert c.is_crisp
    assert c.width == 0
    assert c.defuzzify() == 5


def test_defuzzify_centroid():
    assert TFN(1, 2, 3).defuzzify() == pytest.approx(2.0)
    assert TFN(0, 0, 3).defuzzify() == pytest.approx(1.0)


def test_membership():
    t = TFN(0, 1, 2)
    assert t.membership(1) == pytest.approx(1.0)
    assert t.membership(0.5) == pytest.approx(0.5)
    assert t.membership(0) == 0.0
    assert t.membership(2) == 0.0


def test_alpha_cut():
    lo, hi = TFN(0, 2, 4).alpha_cut(0.5)
    assert lo == pytest.approx(1.0)
    assert hi == pytest.approx(3.0)
    # alpha=1 -> le mode
    lo1, hi1 = TFN(0, 2, 4).alpha_cut(1.0)
    assert lo1 == pytest.approx(2.0) and hi1 == pytest.approx(2.0)


def test_addition_and_scale():
    assert TFN(1, 2, 3) + TFN(1, 1, 1) == TFN(2, 3, 4)
    assert TFN(1, 2, 3).scale(2) == TFN(2, 4, 6)
    with pytest.raises(ValueError):
        TFN(1, 2, 3).scale(-1)


def test_mul_div_positive():
    assert TFN(1, 2, 3) * TFN(1, 2, 3) == TFN(1, 4, 9)
    q = TFN(2, 4, 6) / TFN(1, 2, 3)
    assert q.a == pytest.approx(2 / 3)
    assert q.m == pytest.approx(2.0)
    assert q.b == pytest.approx(6.0)


def test_clamp():
    assert TFN(-0.5, 0, 0.5).clamp(0, 4) == TFN(0, 0, 0.5)


def test_fuzzy_sum():
    assert fuzzy_sum([TFN(1, 1, 1), TFN(2, 2, 2)]) == TFN(3, 3, 3)


def test_weighted_average_uniform():
    res = fuzzy_weighted_average([TFN(2, 2, 2), TFN(4, 4, 4)], [1, 1])
    assert res.defuzzify() == pytest.approx(3.0)


def test_weighted_average_propagates_uncertainty():
    # deux réponses identiques mais incertaines : l'incertitude se conserve
    res = fuzzy_weighted_average([TFN(1, 2, 3), TFN(1, 2, 3)], [1, 1])
    assert res.width > 0


def test_weighted_average_length_mismatch():
    with pytest.raises(ValueError):
        fuzzy_weighted_average([TFN(1, 1, 1)], [1, 2])
