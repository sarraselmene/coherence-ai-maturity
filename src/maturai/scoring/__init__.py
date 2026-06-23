"""Moteur de scoring flou (Étape 2) — cœur scientifique du projet."""

from maturai.scoring.engine import score_assessment
from maturai.scoring.inference import InferenceResult, infer_incoherence_penalty
from maturai.scoring.results import (
    AssessmentScore,
    AxisScore,
    QuestionScore,
    SubDomainScore,
)

__all__ = [
    "score_assessment",
    "AssessmentScore",
    "AxisScore",
    "SubDomainScore",
    "QuestionScore",
    "InferenceResult",
    "infer_incoherence_penalty",
]
