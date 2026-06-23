"""Tests du Fuzzy AHP (pondération inter-axes)."""

from __future__ import annotations

import numpy as np
import pytest

from maturai.domain.fuzzy_number import TriangularFuzzyNumber as TFN
from maturai.weighting.consistency import consistency_ratio
from maturai.weighting.fuzzy_ahp import (
    load_axis_weights,
    saaty_to_tfn,
)


def test_saaty_to_tfn():
    assert saaty_to_tfn(1) == TFN(1, 1, 1)
    assert saaty_to_tfn(3) == TFN(2, 3, 4)
    recip = saaty_to_tfn(1 / 3)
    assert recip.a == pytest.approx(1 / 4)
    assert recip.m == pytest.approx(1 / 3)
    assert recip.b == pytest.approx(1 / 2)


def test_perfectly_consistent_matrix_has_zero_cr():
    # matrice cohérente w = [0.5, 0.25, 0.25] => ratios exacts
    m = np.array([[1, 2, 2], [0.5, 1, 1], [0.5, 1, 1]], dtype=float)
    assert consistency_ratio(m) == pytest.approx(0.0, abs=1e-6)


def test_axis_weights_sum_to_one_and_positive():
    result = load_axis_weights()
    w = result.weights
    assert sum(w.values()) == pytest.approx(1.0, abs=1e-6)
    assert all(v > 0 for v in w.values())


def test_governance_is_dominant():
    result = load_axis_weights()
    w = result.weights
    assert max(w, key=w.get) == "governance"
    # symétries attendues de la matrice
    assert w["strategy"] == pytest.approx(w["data"], abs=1e-6)
    assert w["talents"] == pytest.approx(w["technology"], abs=1e-6)
    assert w["strategy"] > w["talents"]


def test_matrix_is_consistent():
    result = load_axis_weights()
    assert result.is_consistent  # CR <= 0.10


def test_weights_close_to_target():
    # cohérence avec le récapitulatif initial (gouvernance ~0.30-0.37)
    w = load_axis_weights().weights
    assert 0.30 <= w["governance"] <= 0.40
    assert 0.18 <= w["strategy"] <= 0.24
