"""Rendu de rapport **hors-ligne** (déterministe, sans LLM).

Produit un rapport Markdown directement à partir du score structuré, sans appel
réseau ni clé API. Sert (1) de livrable de repli quand le LLM n'est pas
disponible, (2) de base factuelle reproductible que le rapport LLM (étape 6)
viendra enrichir narrativement, (3) de support de test déterministe.

Aucune dépendance externe : génération de chaînes pure.
"""

from __future__ import annotations

from maturai.reporting.kpis import kpis_for_axis
from maturai.roi.monte_carlo import ROIResult
from maturai.scoring.results import AssessmentScore

_SEVERITY_LABEL = {"SMALL": "faible", "MEDIUM": "modérée", "LARGE": "élevée"}


def _fmt(x: float, n: int = 2) -> str:
    return f"{x:.{n}f}"


def render_markdown_report(
    score: AssessmentScore,
    sector: str | None = None,
    roi: ROIResult | None = None,
) -> str:
    """Génère un rapport Markdown complet et déterministe."""
    lo, hi = score.credibility_interval
    lines: list[str] = []
    a = lines.append

    a(f"# Rapport de maturité IA — {score.client_name}")
    if sector:
        a(f"*Secteur : {sector}*")
    a("")

    # 1. Synthèse
    a("## 1. Synthèse")
    a(
        f"Niveau de maturité IA global : **{_fmt(score.presented_level)} / 5** "
        f"(intervalle de crédibilité : {_fmt(lo + 1)}–{_fmt(hi + 1)} sur 5)."
    )
    a(
        f"Score d'agrégation linéaire classique : {_fmt(score.classic_weighted_mean + 1)} / 5 "
        f"— le moteur flou applique un écart net de {_fmt(score.fuzzy_vs_classic_gap)} point(s) "
        f"(dont pénalité d'incohérence {_fmt(score.incoherence_penalty)})."
    )
    a("")

    # 2. Lecture par axe
    a("## 2. Lecture par axe")
    a("| Axe | Niveau /5 | Incertitude | Poids | Niveau dominant |")
    a("|-----|:---------:|:-----------:|:-----:|-----------------|")
    for ax in sorted(score.axes, key=lambda x: x.crisp, reverse=True):
        profile = ax.level_profile()
        dominant = max(profile, key=profile.get) if profile else "—"
        a(
            f"| {ax.name} | {_fmt(ax.presented_level)} | ±{_fmt(ax.uncertainty)} "
            f"| {_fmt(ax.weight)} | {dominant} |"
        )
    a("")

    # 3. Incohérences & risques
    a("## 3. Incohérences & risques détectés")
    if score.fired_rules:
        for r in score.fired_rules:
            sev = _SEVERITY_LABEL.get(r.consequent, r.consequent)
            a(
                f"- **{r.name}** (sévérité {sev}, intensité {_fmt(r.strength)}) — "
                f"{r.description} Axes : {', '.join(r.axes_involved)}."
            )
    else:
        a("- Aucune incohérence inter-axes significative détectée.")
    a("")

    # 4. Recommandations & KPI
    a("## 4. Recommandations prioritaires & KPI de suivi")
    weakest = sorted(score.axes, key=lambda x: x.crisp)[:3]
    a("Axes prioritaires (scores les plus faibles) :")
    for ax in weakest:
        a(f"\n### {ax.name} — niveau {_fmt(ax.presented_level)} / 5")
        a("KPI de suivi recommandés :")
        for kpi in kpis_for_axis(ax.axis_id):
            a(f"- {kpi}")
    a("")

    # 5. ROI (optionnel)
    if roi is not None:
        a("## 5. Impact financier (ROI Monte Carlo)")
        a(f"- ETP économisables (médian) : **{_fmt(roi.fte_saved.median, 1)}** "
          f"(P10 {_fmt(roi.fte_saved.p10, 1)} — P90 {_fmt(roi.fte_saved.p90, 1)})")
        a(f"- Gains annuels estimés (médian) : **{roi.annual_savings.median:,.0f} €**")
        a(f"- ROI médian : **{_fmt(roi.roi_ratio.median)}** "
          f"— probabilité d'un ROI positif : **{roi.prob_roi_positive:.0%}**")
        a("")

    a("---")
    a(f"*Méthode : {score.method}. Rapport généré hors-ligne (déterministe).*")
    return "\n".join(lines)
