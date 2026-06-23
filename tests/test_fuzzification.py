"""Tests de la fuzzification des réponses."""

from __future__ import annotations

import pytest

from maturai.config import ScoringConfig
from maturai.domain.responses import QuestionResponse
from maturai.scoring.fuzzification import (
    fuzzify_response,
    fuzzify_score,
    spread_for_confidence,
)

CFG = ScoringConfig()  # base_spread=0.5, max_extra_spread=1.0


def test_spread_increases_when_confidence_drops():
    assert spread_for_confidence(1.0, CFG) == pytest.approx(0.5)
    assert spread_for_confidence(0.0, CFG) == pytest.approx(1.5)
    assert spread_for_confidence(0.5, CFG) == pytest.approx(1.0)


def test_certain_answer_tfn():
    t = fuzzify_score(2, 1.0, CFG)
    assert (t.a, t.m, t.b) == pytest.approx((1.5, 2.0, 2.5))
    assert t.defuzzify() == pytest.approx(2.0)


def test_low_confidence_widens_support():
    certain = fuzzify_score(2, 1.0, CFG)
    uncertain = fuzzify_score(2, 0.0, CFG)
    assert uncertain.width > certain.width
    # le mode reste inchangé
    assert uncertain.m == pytest.approx(2.0)


def test_clamping_on_bounds():
    t = fuzzify_score(0, 1.0, CFG)
    assert t.a == pytest.approx(0.0)  # -0.5 ramené à 0
    t4 = fuzzify_score(4, 1.0, CFG)
    assert t4.b == pytest.approx(4.0)


def test_fuzzify_response():
    r = QuestionResponse(question_id="Q7", score=3, confidence=1.0)
    t = fuzzify_response(r, CFG)
    assert t.m == pytest.approx(3.0)
