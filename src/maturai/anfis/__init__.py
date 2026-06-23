"""ANFIS — neuro-flou adaptatif (enrichissement point 2). Nécessite l'extra ``fuzzy``."""

from maturai.anfis.model import ANFIS, ANFISConfig
from maturai.anfis.training import (
    ANFISMetrics,
    build_distillation_dataset,
    train_global_anfis,
)

__all__ = [
    "ANFIS",
    "ANFISConfig",
    "ANFISMetrics",
    "build_distillation_dataset",
    "train_global_anfis",
]
