"""Tests d'intégration du moteur de scoring complet (Étape 2)."""

from __future__ import annotations

import pytest

from maturai.scoring.engine import score_assessment
from maturai.validation.profiles import get_profile, make_assessment


def _score(profile_name, referential):
    spec = get_profile(profile_name)
    assessment = make_assessment(spec, referential, confidence=1.0)
    return score_assessment(assessment, referential)


def test_uniform_mid_profile(referential):
    score = _score("Intermédiaire cohérent", referential)
    assert score.global_crisp == pytest.approx(2.0, abs=1e-6)
    assert score.presented_level == pytest.approx(3.0, abs=1e-6)
    assert score.incoherence_penalty == 0.0
    assert score.fuzzy_vs_classic_gap == pytest.approx(0.0, abs=1e-6)
    assert not score.fired_rules


def test_leader_profile_high_score_no_penalty(referential):
    score = _score("Leader cohérent", referential)
    assert score.global_crisp > 3.5
    assert score.incoherence_penalty == 0.0


def test_incoherent_profile_is_penalized(referential):
    score = _score("Incohérent : ambition sans gouvernance", referential)
    assert score.incoherence_penalty > 0.0
    assert score.fired_rules
    # le moteur flou note PLUS BAS que l'agrégation linéaire classique
    assert score.global_crisp < score.classic_weighted_mean


def test_score_bounds(referential):
    for name in [
        "Débutant cohérent",
        "Leader cohérent",
        "Incohérent : déploiement sur données faibles",
    ]:
        score = _score(name, referential)
        assert 0.0 <= score.global_crisp <= 4.0
        assert 1.0 <= score.presented_level <= 5.0


def test_axis_weights_normalized(referential):
    score = _score("Intermédiaire cohérent", referential)
    assert sum(score.axis_weights.values()) == pytest.approx(1.0, abs=1e-6)


def test_result_serialization(referential):
    score = _score("Intermédiaire cohérent", referential)
    d = score.to_dict()
    assert "global" in d and "axes" in d and "incoherences" in d
    assert len(d["axes"]) == 5
    assert "credibility_interval" in d["global"]


def test_credibility_interval_brackets_mode(referential):
    score = _score("Intermédiaire cohérent", referential)
    lo, hi = score.credibility_interval
    assert lo <= score.global_raw_crisp <= hi
