"""Tests du rendu de rapport hors-ligne et du prompt LLM."""

from __future__ import annotations

from maturai.reporting import build_report_prompt, render_markdown_report
from maturai.scoring.engine import score_assessment
from maturai.validation.profiles import get_profile, make_assessment


def _score(referential, name="Incohérent : ambition sans gouvernance"):
    return score_assessment(make_assessment(get_profile(name), referential), referential)


def test_offline_report_contains_sections(referential):
    report = render_markdown_report(_score(referential), sector="Banque/Assurance")
    for heading in ["# Rapport", "## 1. Synthèse", "## 2. Lecture par axe",
                    "## 3. Incohérences", "## 4. Recommandations"]:
        assert heading in report


def test_offline_report_flags_incoherence(referential):
    report = render_markdown_report(_score(referential))
    assert "ambition_sans_gouvernance" in report


def test_offline_report_with_roi(referential):
    from maturai.domain.responses import ROIInputs
    from maturai.roi import build_roi_inputs, simulate_roi

    score = _score(referential)
    roi_inputs = ROIInputs(hours_per_week=300, cost_per_fte=60000, ai_budget=200000,
                           measured_gains="Estimés", risk_cost="Non")
    roi = simulate_roi(build_roi_inputs(roi_inputs, (score.global_tfn.a, score.global_tfn.m,
                                                     score.global_tfn.b)), n_simulations=1000)
    report = render_markdown_report(score, roi=roi)
    assert "## 5. Impact financier" in report


def test_prompt_includes_sector_and_scores(referential):
    prompt = build_report_prompt(_score(referential), sector="Santé")
    assert "Santé" in prompt
    assert "niveau_global_sur_5" in prompt  # le score structuré est injecté
