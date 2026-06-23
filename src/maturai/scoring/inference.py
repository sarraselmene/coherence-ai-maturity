"""Système d'inférence de Mamdani pour les incohérences inter-axes.

Pipeline Mamdani standard :

1. **Fuzzification** des scores d'axes (déjà défuzzifiés depuis leurs TFN) en
   degrés d'appartenance LOW/MED/HIGH.
2. **Évaluation des règles** : chaque règle d'incohérence produit une force
   d'activation ``alpha`` (combinaison AND=min / OR=max de ses antécédents).
3. **Implication** : l'ensemble de pénalité conséquent est *écrêté* à ``alpha``
   (implication de Mamdani, min).
4. **Agrégation** des conséquents écrêtés par maximum sur toutes les règles.
5. **Défuzzification** par centroïde → pénalité crisp.

La pénalité (en unités de score, dans ``[0, PENALTY_UNIVERSE_MAX]``) est ensuite
soustraite au score global brut par le moteur. Les règles activées au-delà d'un
seuil sont remontées comme **incohérences détectées** (exploitables par le
rapport LLM).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from maturai.config import DEFAULT_SCORING, ScoringConfig
from maturai.scoring.defuzzification import centroid_of_samples
from maturai.scoring.membership import trimf
from maturai.scoring.rules import (
    INCOHERENCE_RULES,
    PENALTY_SETS,
    PENALTY_UNIVERSE_MAX,
    IncoherenceRule,
)


@dataclass(frozen=True)
class FiredRule:
    """Trace d'une règle activée (pour explication et rapport)."""

    name: str
    description: str
    strength: float
    axes_involved: tuple[str, ...]
    consequent: str


@dataclass(frozen=True)
class InferenceResult:
    """Résultat de l'inférence Mamdani d'incohérence."""

    penalty: float  # pénalité crisp à soustraire au score global
    fired_rules: list[FiredRule]

    @property
    def has_incoherence(self) -> bool:
        return bool(self.fired_rules)


def infer_incoherence_penalty(
    axis_scores: dict[str, float],
    rules: list[IncoherenceRule] = INCOHERENCE_RULES,
    config: ScoringConfig = DEFAULT_SCORING,
    *,
    activation_threshold: float = 1e-3,
    n_samples: int = 201,
) -> InferenceResult:
    """Calcule la pénalité d'incohérence par inférence de Mamdani.

    Args:
        axis_scores: scores crisp par axe (défuzzifiés), sur ``[0, 4]``.
        rules: base de règles à évaluer.
        config: hyperparamètres (``incoherence_enabled``, ``incoherence_strength``).
        activation_threshold: force minimale pour qu'une règle soit remontée.
        n_samples: finesse d'échantillonnage de l'univers de pénalité.
    """
    if not config.incoherence_enabled:
        return InferenceResult(penalty=0.0, fired_rules=[])

    universe = np.linspace(0.0, PENALTY_UNIVERSE_MAX, n_samples)
    aggregated = np.zeros_like(universe)
    fired: list[FiredRule] = []

    for rule in rules:
        alpha = float(rule.antecedent(axis_scores))
        if alpha <= 0.0:
            continue
        # Implication de Mamdani : écrêtage du conséquent à alpha
        a, b, c = PENALTY_SETS[rule.consequent]
        clipped = np.minimum(alpha, np.array([trimf(p, a, b, c) for p in universe]))
        # Agrégation par maximum
        aggregated = np.maximum(aggregated, clipped)
        if alpha >= activation_threshold:
            fired.append(
                FiredRule(
                    name=rule.name,
                    description=rule.description,
                    strength=alpha,
                    axes_involved=rule.axes_involved,
                    consequent=rule.consequent,
                )
            )

    penalty = centroid_of_samples(universe, aggregated) if aggregated.sum() > 0 else 0.0
    penalty *= config.incoherence_strength
    fired.sort(key=lambda r: r.strength, reverse=True)
    return InferenceResult(penalty=penalty, fired_rules=fired)
