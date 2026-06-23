"""Tests de la réconciliation Graph-RAG (avec extracteur mock)."""

from __future__ import annotations

from maturai.domain.responses import Assessment, QuestionResponse
from maturai.graphrag import MockEvidenceExtractor, detect_coherence, reconcile
from maturai.graphrag.interfaces import EvidenceSuggestion


def _extractor():
    return MockEvidenceExtractor(
        {
            "Q28": [EvidenceSuggestion("Q28", 4, 0.9, "charte publiée", "charte_ia.pdf")],
            "Q29": [EvidenceSuggestion("Q29", 2, 0.8, "registre partiel", "audit.pdf")],
        }
    )


def test_detect_coherence_flags_large_gap():
    declared = {"Q28": 0, "Q29": 2}
    evidence = _extractor().suggest_all(["Q28", "Q29"])
    findings = detect_coherence(declared, evidence, tolerance=1)
    ids = {f.question_id for f in findings}
    assert "Q28" in ids  # déclaré 0 vs preuve 4 -> contradiction
    assert "Q29" not in ids  # déclaré 2 vs preuve 2 -> accord


def test_contradiction_lowers_confidence():
    assessment = Assessment(
        responses=[QuestionResponse(question_id="Q28", score=0, confidence=1.0)]
    )
    res = reconcile(assessment, _extractor(), fill_unanswered=False)
    q28 = res.assessment.responses_by_id()["Q28"]
    assert q28.confidence < 1.0  # preuve contredit -> incertitude accrue
    assert q28.source == "reconciled"
    assert res.n_contradicted == 1


def test_agreement_preserves_or_boosts_confidence():
    assessment = Assessment(
        responses=[QuestionResponse(question_id="Q29", score=2, confidence=0.7)]
    )
    res = reconcile(assessment, _extractor(), fill_unanswered=False)
    q29 = res.assessment.responses_by_id()["Q29"]
    assert q29.confidence >= 0.7


def test_unanswered_questions_are_prefilled():
    assessment = Assessment(responses=[QuestionResponse(question_id="Q29", score=2)])
    res = reconcile(assessment, _extractor(), fill_unanswered=True)
    ids = res.assessment.responses_by_id()
    assert "Q28" in ids  # pré-rempli depuis la preuve
    assert ids["Q28"].source == "graph_rag"
    assert any(s.question_id == "Q28" for s in res.suggested)


def test_lower_confidence_widens_downstream_uncertainty():
    from maturai.scoring.fuzzification import fuzzify_response

    high = QuestionResponse(question_id="Q1", score=2, confidence=1.0)
    low = QuestionResponse(question_id="Q1", score=2, confidence=0.3)
    assert fuzzify_response(low).width > fuzzify_response(high).width
