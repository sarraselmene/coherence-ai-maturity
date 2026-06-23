"""Base de règles floues pour la détection d'incohérences inter-axes.

Motivation
----------
Une organisation peut afficher une **stratégie IA ambitieuse** tout en ayant une
**gouvernance défaillante**. Une moyenne pondérée classique lisserait ces deux
signaux en un score « moyen » rassurant, masquant un profil en réalité risqué.
La logique floue, via un système d'inférence de **Mamdani**, permet d'exprimer
explicitement ces patterns à risque sous forme de règles linguistiques et de
calculer une **pénalité de cohérence** appliquée au score global.

Termes linguistiques par axe (univers du score : ``[0, 4]``)
------------------------------------------------------------
* ``LOW``  : (0, 0, 2)
* ``MED``  : (1, 2, 3)
* ``HIGH`` : (2, 4, 4)

Pénalité (univers ``[0, PENALTY_UNIVERSE_MAX]`` en unités de score)
* ``SMALL``  : (0, 0, 0.5)
* ``MEDIUM`` : (0.25, 0.5, 0.75)
* ``LARGE``  : (0.5, 1.0, 1.0)

Chaque règle déclare un antécédent (combinaison floue AND=min / OR=max de termes
d'axes) et un conséquent (un ensemble de pénalité). Les règles sont **données**,
pas codées en dur dans le moteur : on peut les auditer, les compléter et, à
terme, les **apprendre** (ANFIS, enrichissement point 2) sans toucher au moteur.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from maturai.scoring.membership import trimf

PENALTY_UNIVERSE_MAX = 1.0

# --- Termes linguistiques sur le score d'un axe [0, 4] -------------------- #
_AXIS_TERMS: dict[str, tuple[float, float, float]] = {
    "LOW": (0.0, 0.0, 2.0),
    "MED": (1.0, 2.0, 3.0),
    "HIGH": (2.0, 4.0, 4.0),
}

# --- Ensembles de pénalité sur [0, PENALTY_UNIVERSE_MAX] ------------------- #
PENALTY_SETS: dict[str, tuple[float, float, float]] = {
    "SMALL": (0.0, 0.0, 0.5),
    "MEDIUM": (0.25, 0.5, 0.75),
    "LARGE": (0.5, 1.0, 1.0),
}


def axis_term_degree(score: float, term: str) -> float:
    """Degré d'appartenance d'un score d'axe à un terme (LOW/MED/HIGH)."""
    return trimf(score, *_AXIS_TERMS[term])


# Type d'un antécédent : fonction (scores d'axes) -> force d'activation [0, 1]
Antecedent = Callable[[dict[str, float]], float]


@dataclass(frozen=True)
class IncoherenceRule:
    """Une règle floue d'incohérence inter-axes."""

    name: str
    description: str
    antecedent: Antecedent
    consequent: str  # clé de PENALTY_SETS
    axes_involved: tuple[str, ...]


def _deg(scores: dict[str, float], axis: str, term: str) -> float:
    return axis_term_degree(scores[axis], term)


# --------------------------------------------------------------------------- #
# Base de règles. AND = min, OR = max.
# --------------------------------------------------------------------------- #
INCOHERENCE_RULES: list[IncoherenceRule] = [
    IncoherenceRule(
        name="ambition_sans_gouvernance",
        description=(
            "Stratégie OU technologie élevée alors que la gouvernance est faible : "
            "déploiement/ambition IA sans cadre de maîtrise des risques."
        ),
        antecedent=lambda s: min(
            max(_deg(s, "strategy", "HIGH"), _deg(s, "technology", "HIGH")),
            _deg(s, "governance", "LOW"),
        ),
        consequent="LARGE",
        axes_involved=("strategy", "technology", "governance"),
    ),
    IncoherenceRule(
        name="deploiement_sur_donnees_faibles",
        description=(
            "Technologie élevée alors que la maturité Données est faible : "
            "modèles déployés sur un socle de données non maîtrisé."
        ),
        antecedent=lambda s: min(_deg(s, "technology", "HIGH"), _deg(s, "data", "LOW")),
        consequent="MEDIUM",
        axes_involved=("technology", "data"),
    ),
    IncoherenceRule(
        name="ambition_sans_talents",
        description=(
            "Stratégie élevée alors que les talents/compétences sont faibles : "
            "ambition non soutenue par la capacité d'exécution."
        ),
        antecedent=lambda s: min(_deg(s, "strategy", "HIGH"), _deg(s, "talents", "LOW")),
        consequent="MEDIUM",
        axes_involved=("strategy", "talents"),
    ),
]
# Note de conception : toutes les règles détectent un *écart* (un axe HIGH face à
# un axe LOW). Un profil uniformément bas n'est PAS une incohérence (c'est une
# faible maturité, déjà reflétée par le score) : aucune règle ne s'y déclenche.
