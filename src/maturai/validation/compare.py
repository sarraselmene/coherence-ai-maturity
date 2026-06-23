"""Comparaison quantitative : scoring classique vs flou (Étape 3 / point 4).

Calcule, sur un ensemble de profils, le score par **moyenne pondérée classique**
et par le **moteur flou** (avec inférence d'incohérence), puis l'écart entre les
deux. Hypothèse à vérifier empiriquement :

* sur les profils **cohérents**, l'écart est faible (le moteur n'invente pas de
  pénalité) ;
* sur les profils **incohérents**, le moteur flou produit un score nettement
  plus bas et détecte des incohérences — ce que la moyenne classique ignore.

Le tableau renvoyé est directement exploitable dans le mémoire (chapitre
validation). L'extension à un troisième scoring (neuro-flou / ANFIS) viendra
brancher la même interface une fois le modèle entraîné.
"""

from __future__ import annotations

from dataclasses import dataclass

from maturai.domain.referential import Referential
from maturai.scoring.engine import score_assessment
from maturai.validation.profiles import ProfileSpec, make_assessment


@dataclass(frozen=True)
class ComparisonRow:
    profile: str
    is_coherent: bool
    classic: float
    fuzzy: float
    gap: float  # fuzzy - classic
    penalty: float
    n_incoherences: int

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "is_coherent": self.is_coherent,
            "classic": round(self.classic, 3),
            "fuzzy": round(self.fuzzy, 3),
            "gap": round(self.gap, 3),
            "penalty": round(self.penalty, 3),
            "n_incoherences": self.n_incoherences,
        }


def compare_profiles(
    profiles: list[ProfileSpec],
    referential: Referential,
    *,
    confidence: float = 1.0,
    seed: int = 0,
) -> list[ComparisonRow]:
    """Compare scoring classique et flou sur une liste de profils."""
    rows: list[ComparisonRow] = []
    for spec in profiles:
        assessment = make_assessment(spec, referential, confidence=confidence, seed=seed)
        score = score_assessment(assessment, referential)
        rows.append(
            ComparisonRow(
                profile=spec.name,
                is_coherent=spec.is_coherent,
                classic=score.classic_weighted_mean,
                fuzzy=score.global_crisp,
                gap=score.fuzzy_vs_classic_gap,
                penalty=score.incoherence_penalty,
                n_incoherences=len(score.fired_rules),
            )
        )
    return rows


def summarize(rows: list[ComparisonRow]) -> dict[str, float]:
    """Statistiques agrégées : écart moyen sur profils cohérents vs incohérents."""
    coherent = [r.gap for r in rows if r.is_coherent]
    incoherent = [r.gap for r in rows if not r.is_coherent]
    return {
        "mean_gap_coherent": sum(coherent) / len(coherent) if coherent else 0.0,
        "mean_gap_incoherent": sum(incoherent) / len(incoherent) if incoherent else 0.0,
        "mean_penalty_incoherent": (
            sum(r.penalty for r in rows if not r.is_coherent)
            / max(1, sum(1 for r in rows if not r.is_coherent))
        ),
    }
