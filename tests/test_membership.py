"""Tests des fonctions d'appartenance de niveau."""

from __future__ import annotations

import pytest

from maturai.scoring.membership import (
    dominant_level,
    level_degrees,
    membership_vector,
    trimf,
)


def test_trimf_shoulders():
    assert trimf(0, 0, 0, 1) == pytest.approx(1.0)
    assert trimf(0.5, 0, 0, 1) == pytest.approx(0.5)
    assert trimf(1, 0, 0, 1) == pytest.approx(0.0)
    assert trimf(4, 3, 4, 4) == pytest.approx(1.0)


def test_membership_vector_integer():
    vec = membership_vector(2)
    assert vec[2] == pytest.approx(1.0)
    assert vec.sum() == pytest.approx(1.0)


@pytest.mark.parametrize("x", [0.0, 0.7, 1.5, 2.4, 3.3, 4.0])
def test_partition_of_unity(x):
    # Les MF triangulaires forment une partition de l'unité sur [0,4].
    assert membership_vector(x).sum() == pytest.approx(1.0, abs=1e-9)


def test_intermediate_membership():
    deg = level_degrees(2.5)
    assert deg["Défini"] == pytest.approx(0.5)
    assert deg["Géré"] == pytest.approx(0.5)


def test_dominant_level():
    assert dominant_level(2.4) == 2  # Défini domine Géré
    assert dominant_level(2.6) == 3
