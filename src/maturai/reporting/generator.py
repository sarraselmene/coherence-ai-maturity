"""Génération du rapport narratif par LLM (Étape 6 / couche 4).

Transforme le score structuré (issu du moteur flou) en un rapport d'aide à la
décision : synthèse narrative, recommandations contextualisées au secteur, et
KPI de suivi par axe.

Séparation des responsabilités :

* :func:`build_report_prompt` construit le **prompt structuré** à partir du
  score, du contexte sectoriel et du catalogue de KPI. C'est du code pur,
  testable, sans dépendance réseau — le cœur de l'ingénierie de prompt.
* :class:`ReportGenerator.generate` réalise l'appel LLM (import paresseux du SDK
  Anthropic). Nécessite ``ANTHROPIC_API_KEY`` et l'extra ``report``.

Le LLM reçoit des **faits déjà calculés** (scores, incohérences détectées,
incertitude) et a pour seule tâche de les *expliquer et contextualiser* : il
n'invente ni score ni métrique, ce qui borne le risque d'hallucination.
"""

from __future__ import annotations

import json
import os

from maturai.reporting.kpis import kpis_for_axis
from maturai.scoring.results import AssessmentScore

SYSTEM_PROMPT = (
    "Tu es un consultant senior de KPMG spécialiste de la transformation IA. "
    "Tu rédiges un rapport d'évaluation de maturité IA factuel, nuancé et "
    "actionnable, en français. Tu t'appuies STRICTEMENT sur les scores et les "
    "incohérences fournis : tu ne réévalues aucun score et n'inventes aucune "
    "donnée chiffrée. Tu cites les niveaux sur l'échelle 1 à 5."
)


def _score_brief(score: AssessmentScore) -> dict:
    """Sérialise le score en un objet compact destiné au prompt."""
    return {
        "client": score.client_name,
        "niveau_global_sur_5": round(score.presented_level, 2),
        "intervalle_credibilite_sur_4": list(score.credibility_interval),
        "incoherences_detectees": [
            {
                "nom": r.name,
                "explication": r.description,
                "intensite": round(r.strength, 2),
                "axes": list(r.axes_involved),
            }
            for r in score.fired_rules
        ],
        "axes": [
            {
                "axe": ax.name,
                "niveau_sur_5": round(ax.presented_level, 2),
                "incertitude": round(ax.uncertainty, 2),
                "profil_niveaux": ax.level_profile(),
                "kpi_suivi": kpis_for_axis(ax.axis_id),
            }
            for ax in score.axes
        ],
    }


def build_report_prompt(score: AssessmentScore, sector: str | None = None) -> str:
    """Construit le prompt utilisateur structuré (code pur, testable)."""
    brief = _score_brief(score)
    sector_line = f"Secteur du client : {sector}." if sector else "Secteur non précisé."
    return (
        f"{sector_line}\n\n"
        "Voici le résultat structuré de l'évaluation de maturité IA "
        "(scores déjà calculés par un moteur de logique floue) :\n\n"
        f"{json.dumps(brief, ensure_ascii=False, indent=2)}\n\n"
        "Rédige un rapport structuré en quatre parties :\n"
        "1. SYNTHÈSE — positionnement global sur l'échelle 1-5, en intégrant "
        "l'intervalle de crédibilité (ne pas présenter le score comme exact).\n"
        "2. LECTURE PAR AXE — forces et faiblesses, en t'appuyant sur le profil "
        "d'appartenance aux niveaux.\n"
        "3. INCOHÉRENCES & RISQUES — explique chaque incohérence détectée et ses "
        "conséquences concrètes pour ce secteur.\n"
        "4. RECOMMANDATIONS & KPI — 3 à 5 recommandations priorisées, et pour "
        "chaque axe les KPI de suivi pertinents parmi ceux fournis.\n"
    )


class ReportGenerator:
    """Génère le rapport via le SDK Anthropic (import paresseux)."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

    def generate(self, score: AssessmentScore, sector: str | None = None) -> str:
        """Appelle le LLM et renvoie le rapport narratif.

        Raises:
            ImportError: si l'extra ``report`` n'est pas installé.
            RuntimeError: si ``ANTHROPIC_API_KEY`` est absent.
        """
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - dépendance optionnelle
            raise ImportError(
                'Génération de rapport : pip install -e ".[report]"'
            ) from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY manquant (cf. .env).")

        client = anthropic.Anthropic()
        message = client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_report_prompt(score, sector)}],
        )
        return "".join(block.text for block in message.content if block.type == "text")
