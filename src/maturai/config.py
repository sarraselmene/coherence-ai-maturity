"""Configuration centrale et chemins du projet.

Centralise (1) les chemins vers les artefacts de données et (2) les
**hyperparamètres du moteur de scoring**. Regrouper ces constantes ici les rend
explicites, traçables dans le mémoire, et faciles à faire varier dans le
protocole de validation (étape 3).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# Chemins
# --------------------------------------------------------------------------- #
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DATA_DIR = PROJECT_ROOT / "data"
REFERENTIAL_PATH = DATA_DIR / "referential" / "questions.json"
REFERENTIAL_SCHEMA_PATH = DATA_DIR / "referential" / "schema" / "questions.schema.json"
AHP_PAIRWISE_PATH = DATA_DIR / "weights" / "ahp_pairwise.json"
PROFILES_DIR = DATA_DIR / "profiles"
CORPUS_DIR = DATA_DIR / "corpus"


@dataclass(frozen=True)
class ScoringConfig:
    """Hyperparamètres du moteur de scoring flou.

    Attributes:
        scale_min / scale_max: bornes de l'univers des scores (0..4).
        base_spread: demi-largeur du TFN issu d'une réponse *certaine*.
            Traduit l'idée méthodologique « une réponse réelle est rarement
            strictement à un niveau » : même certaine, une réponse à k est
            fuzzifiée en TFN(k - s, k, k + s).
        max_extra_spread: incertitude additionnelle maximale ajoutée quand la
            confiance tombe à 0 (réponse non fiable / non corroborée).
        incoherence_enabled: active la couche d'inférence Mamdani inter-axes.
        incoherence_strength: intensité de la pénalité d'incohérence dans [0, 1].
    """

    scale_min: float = 0.0
    scale_max: float = 4.0
    base_spread: float = 0.5
    max_extra_spread: float = 1.0
    incoherence_enabled: bool = True
    incoherence_strength: float = 1.0


DEFAULT_SCORING = ScoringConfig()


@dataclass(frozen=True)
class Neo4jConfig:
    """Connexion Neo4j (Graph-RAG, étape 5). Lue depuis l'environnement."""

    uri: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.environ.get("NEO4J_USER", "neo4j")
    password: str = os.environ.get("NEO4J_PASSWORD", "change-me-please")
    database: str = os.environ.get("NEO4J_DATABASE", "neo4j")
