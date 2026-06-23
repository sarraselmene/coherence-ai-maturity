"""Démonstration de bout en bout du cœur scientifique (Étapes 1-4).

Exécute, sans interface ni LLM, l'enchaînement :
  référentiel → Fuzzy AHP → fuzzification → agrégation → inférence → score
  → ROI Monte Carlo → réconciliation Graph-RAG (mock) → prompt de rapport.

Usage :
    python scripts/run_scoring_demo.py
"""

from __future__ import annotations

import sys

# La console Windows utilise cp1252 par défaut : on force l'UTF-8 pour les
# caractères accentués et les flèches (→, ±).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from maturai.graphrag import MockEvidenceExtractor, detect_coherence
from maturai.referential import coverage_report, get_default_referential
from maturai.reporting import build_report_prompt
from maturai.roi import build_roi_inputs, simulate_roi
from maturai.scoring import score_assessment
from maturai.validation import STANDARD_PROFILES, compare_profiles, make_assessment, summarize
from maturai.weighting import load_axis_weights


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    ref = get_default_referential()

    section("ÉTAPE 1 — Référentiel (double ancrage générique / IA-spécifique)")
    print(f"Questions notées : {ref.n_scored_questions}")
    for axis_id, c in coverage_report(ref).items():
        print(
            f"  {axis_id:<11} total={c['total']:>2}  "
            f"générique={c['generic']:>2}  IA-spécifique={c['ai_specific']:>2}"
        )

    section("ÉTAPE 1b — Pondération inter-axes par Fuzzy AHP")
    ahp = load_axis_weights()
    print(f"Cohérence (CR) = {ahp.consistency_ratio:.4f}  "
          f"(seuil 0.10 → {'OK' if ahp.is_consistent else 'À RÉVISER'})")
    for axis_id, w in ahp.weights.items():
        print(f"  {axis_id:<11} poids = {w:.3f}   (Chang : {ahp.chang_weights[axis_id]:.3f})")

    section("ÉTAPES 2-3 — Scoring flou vs classique sur les profils simulés")
    rows = compare_profiles(STANDARD_PROFILES, ref)
    print(f"{'Profil':<42}{'classique':>10}{'flou':>8}{'écart':>8}{'incoh.':>8}")
    for r in rows:
        print(
            f"{r.profile:<42}{r.classic:>10.2f}{r.fuzzy:>8.2f}{r.gap:>8.2f}{r.n_incoherences:>8}"
        )
    stats = summarize(rows)
    print(
        f"\nÉcart moyen  cohérents = {stats['mean_gap_coherent']:.3f}  |  "
        f"incohérents = {stats['mean_gap_incoherent']:.3f}"
    )
    print("→ Le moteur flou pénalise spécifiquement les profils incohérents.")

    section("Détail d'un profil incohérent")
    spec = next(p for p in STANDARD_PROFILES if not p.is_coherent)
    assessment = make_assessment(spec, ref, confidence=1.0)
    score = score_assessment(assessment, ref)
    print(f"Profil : {spec.name}")
    print(f"Niveau global présenté : {score.presented_level:.2f} / 5")
    print(f"Intervalle de crédibilité (sur 4) : "
          f"[{score.credibility_interval[0]:.2f}, {score.credibility_interval[1]:.2f}]")
    print(f"Pénalité d'incohérence : {score.incoherence_penalty:.3f}")
    print("Incohérences détectées :")
    for r in score.fired_rules:
        print(f"  - {r.name} (intensité {r.strength:.2f}) : {r.description}")
    print("Scores par axe :")
    for ax in score.axes:
        print(f"  {ax.name:<28} {ax.presented_level:.2f}/5  (±{ax.uncertainty:.2f})")

    section("ÉTAPE 4 — ROI Monte Carlo (consomme la maturité + son incertitude)")
    assessment.roi_inputs.hours_per_week = 350
    assessment.roi_inputs.cost_per_fte = 62_000
    assessment.roi_inputs.ai_budget = 250_000
    assessment.roi_inputs.measured_gains = "Estimés"
    assessment.roi_inputs.risk_cost = "Estimation grossière"
    roi = simulate_roi(
        build_roi_inputs(
            assessment.roi_inputs,
            (score.global_tfn.a, score.global_tfn.m, score.global_tfn.b),
        )
    )
    print(f"ETP économisables (médian)   : {roi.fte_saved.median:.1f} "
          f"[P10={roi.fte_saved.p10:.1f} ; P90={roi.fte_saved.p90:.1f}]")
    print(f"Gains annuels € (médian)     : {roi.annual_savings.median:,.0f}")
    print(f"ROI (médian)                 : {roi.roi_ratio.median:.2f}")
    print(f"P(ROI > 0)                   : {roi.prob_roi_positive:.0%}")

    section("ÉTAPE 5 — Réconciliation Graph-RAG (extracteur mock)")
    extractor = MockEvidenceExtractor()
    declared = {r.question_id: r.score for r in assessment.responses}
    evidence = extractor.suggest_all(list(declared.keys()))
    findings = detect_coherence(declared, evidence)
    if findings:
        for f in findings:
            print(f"  Q{f.question_id[1:]} : déclaré {f.declared_score} vs preuve "
                  f"{f.evidence_score}  ← {f.source_document}")
    else:
        print("  Aucun écart significatif entre réponses déclarées et preuves (mock).")

    section("ÉTAPE 6 — Prompt de rapport LLM (aperçu, sans appel réseau)")
    prompt = build_report_prompt(score, sector="Banque/Assurance")
    print(prompt[:600] + "\n[... tronqué ...]")


if __name__ == "__main__":
    main()
