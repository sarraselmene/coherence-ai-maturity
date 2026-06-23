"""Règles d'inférence floue (incohérences inter-axes)."""

from maturai.scoring.rules.incoherence_rules import (
    INCOHERENCE_RULES,
    PENALTY_SETS,
    PENALTY_UNIVERSE_MAX,
    IncoherenceRule,
    axis_term_degree,
)

__all__ = [
    "INCOHERENCE_RULES",
    "PENALTY_SETS",
    "PENALTY_UNIVERSE_MAX",
    "IncoherenceRule",
    "axis_term_degree",
]
