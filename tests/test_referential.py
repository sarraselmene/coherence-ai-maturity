"""Tests du chargement et de la validation du référentiel (Étape 1)."""

from __future__ import annotations

import pytest

from maturai.referential.validators import (
    ReferentialError,
    coverage_report,
    validate_referential,
)


def test_loads_successfully(referential):
    assert referential.meta.name
    assert len(referential.axes) == 5


def test_question_count(referential):
    # 31 questions initiales + Q15bis + Q18bis (couche IA-spécifique Données)
    assert referential.n_scored_questions == 33


def test_unique_question_ids(referential):
    ids = referential.question_ids()
    assert len(ids) == len(set(ids))


def test_axes_present(referential):
    ids = {ax.id for ax in referential.axes}
    assert ids == {"strategy", "data", "talents", "technology", "governance"}


def test_coverage_double_anchor(referential):
    report = coverage_report(referential)
    # Données : 8 questions dont 2 IA-spécifiques (Q15bis lineage de biais, Q18bis)
    assert report["data"]["total"] == 8
    assert report["data"]["ai_specific"] == 2
    # Gouvernance : 10 questions dont 7 IA-spécifiques (Q31..Q37)
    assert report["governance"]["total"] == 10
    assert report["governance"]["ai_specific"] == 7


def test_every_question_has_five_levels(referential):
    for q in referential.iter_scored_questions():
        assert [lvl.score for lvl in q.levels] == [0, 1, 2, 3, 4]


def test_every_question_is_traceable(referential):
    known = set(referential.meta.referential_sources.keys())
    for q in referential.iter_scored_questions():
        assert q.referential.sources
        assert set(q.referential.sources).issubset(known)
        assert q.referential.justification


def test_validation_rejects_zero_weight(referential):
    ref = referential.model_copy(deep=True)
    ref.axes[0].weight = 0.0
    with pytest.raises(ReferentialError):
        validate_referential(ref)


def test_validation_rejects_unknown_source(referential):
    ref = referential.model_copy(deep=True)
    ref.axes[0].subdomains[0].questions[0].referential.sources = ["INCONNU"]
    with pytest.raises(ReferentialError):
        validate_referential(ref)
