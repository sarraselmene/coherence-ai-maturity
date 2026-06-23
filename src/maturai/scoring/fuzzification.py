"""Fuzzification : réponse crisp → nombre flou triangulaire (TFN).

C'est l'étape d'entrée du moteur. Une réponse à la question vaut un entier
``k ∈ {0..4}``, mais on ne la traite pas comme une certitude ponctuelle : on la
convertit en TFN ``(k - s, k, k + s)`` borné sur ``[0, 4]``.

La demi-largeur ``s`` encode **deux sources d'incertitude** :

* une incertitude *irréductible* ``base_spread`` : même une réponse assumée
  reste une approximation d'une réalité organisationnelle nuancée (fondement
  méthodologique du sujet) ;
* une incertitude *liée à la fiabilité* : plus la confiance dans la réponse est
  faible (réponse non corroborée par le Graph-RAG, répondant peu légitime…),
  plus le support s'élargit — jusqu'à ``base_spread + max_extra_spread``.

    s = base_spread + (1 - confidence) · max_extra_spread

Ainsi l'incertitude se propage *dès l'entrée* et traverse toute l'agrégation
(point 3 de la feuille de route).
"""

from __future__ import annotations

from maturai.config import DEFAULT_SCORING, ScoringConfig
from maturai.domain.fuzzy_number import TriangularFuzzyNumber as TFN
from maturai.domain.responses import QuestionResponse


def spread_for_confidence(confidence: float, config: ScoringConfig = DEFAULT_SCORING) -> float:
    """Demi-largeur du TFN en fonction de la confiance dans ``[0, 1]``."""
    confidence = min(max(confidence, 0.0), 1.0)
    return config.base_spread + (1.0 - confidence) * config.max_extra_spread


def fuzzify_score(
    score: float,
    confidence: float = 1.0,
    config: ScoringConfig = DEFAULT_SCORING,
) -> TFN:
    """Fuzzifie un score crisp en TFN borné sur l'univers ``[scale_min, scale_max]``."""
    s = spread_for_confidence(confidence, config)
    return TFN(score - s, score, score + s).clamp(config.scale_min, config.scale_max)


def fuzzify_response(
    response: QuestionResponse,
    config: ScoringConfig = DEFAULT_SCORING,
) -> TFN:
    """Fuzzifie une :class:`QuestionResponse`."""
    return fuzzify_score(response.score, response.confidence, config)
