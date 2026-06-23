"""Structures de résultat du moteur de scoring.

Objets immuables et sérialisables (``to_dict``) décrivant le score à chaque
niveau de la hiérarchie, l'incertitude associée (issue des TFN) et les
incohérences détectées. Ces objets sont l'**interface de sortie** du cœur
scientifique : ils alimentent le module ROI (point 6), le rapport LLM (étape 6)
et l'interface web (étape 7).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from maturai.domain.fuzzy_number import TriangularFuzzyNumber as TFN
from maturai.scoring.inference import FiredRule
from maturai.scoring.membership import level_degrees


def _to_presented(crisp: float) -> float:
    """Convertit un score interne [0,4] en niveau présenté [1,5]."""
    return crisp + 1.0


@dataclass(frozen=True)
class QuestionScore:
    question_id: str
    layer: str
    tfn: TFN
    crisp: float

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "layer": self.layer,
            "tfn": [self.tfn.a, self.tfn.m, self.tfn.b],
            "crisp": round(self.crisp, 4),
        }


@dataclass(frozen=True)
class SubDomainScore:
    subdomain_id: str
    name: str
    tfn: TFN
    crisp: float
    questions: list[QuestionScore] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "subdomain_id": self.subdomain_id,
            "name": self.name,
            "crisp": round(self.crisp, 4),
            "tfn": [self.tfn.a, self.tfn.m, self.tfn.b],
            "questions": [q.to_dict() for q in self.questions],
        }


@dataclass(frozen=True)
class AxisScore:
    axis_id: str
    name: str
    tfn: TFN
    crisp: float
    weight: float
    subdomains: list[SubDomainScore] = field(default_factory=list)

    @property
    def presented_level(self) -> float:
        return _to_presented(self.crisp)

    @property
    def uncertainty(self) -> float:
        """Largeur du support du TFN d'axe (mesure d'incertitude)."""
        return self.tfn.width

    def level_profile(self) -> dict[str, float]:
        """Profil d'appartenance du score d'axe aux 5 niveaux CMMI."""
        return level_degrees(self.crisp)

    def to_dict(self) -> dict:
        return {
            "axis_id": self.axis_id,
            "name": self.name,
            "crisp": round(self.crisp, 4),
            "presented_level": round(self.presented_level, 4),
            "tfn": [self.tfn.a, self.tfn.m, self.tfn.b],
            "uncertainty": round(self.uncertainty, 4),
            "weight": round(self.weight, 4),
            "level_profile": {k: round(v, 4) for k, v in self.level_profile().items()},
            "subdomains": [sd.to_dict() for sd in self.subdomains],
        }


@dataclass(frozen=True)
class AssessmentScore:
    """Résultat global d'une évaluation."""

    client_name: str
    axes: list[AxisScore]
    global_tfn: TFN
    global_raw_crisp: float  # score global flou défuzzifié, avant pénalité
    incoherence_penalty: float
    global_crisp: float  # score global final = raw - pénalité, borné
    fired_rules: list[FiredRule]
    classic_weighted_mean: float  # baseline d'agrégation linéaire (pour comparaison)
    credibility_interval: tuple[float, float]  # alpha-cut du TFN global
    axis_weights: dict[str, float]
    method: str = "fuzzy_mamdani_hierarchical_tfn"

    @property
    def presented_level(self) -> float:
        return _to_presented(self.global_crisp)

    @property
    def fuzzy_vs_classic_gap(self) -> float:
        """Écart score flou (final) − moyenne classique : l'effet net du moteur."""
        return self.global_crisp - self.classic_weighted_mean

    def to_dict(self) -> dict:
        return {
            "client_name": self.client_name,
            "method": self.method,
            "global": {
                "crisp": round(self.global_crisp, 4),
                "raw_crisp": round(self.global_raw_crisp, 4),
                "presented_level": round(self.presented_level, 4),
                "tfn": [self.global_tfn.a, self.global_tfn.m, self.global_tfn.b],
                "credibility_interval": [
                    round(self.credibility_interval[0], 4),
                    round(self.credibility_interval[1], 4),
                ],
                "incoherence_penalty": round(self.incoherence_penalty, 4),
                "classic_weighted_mean": round(self.classic_weighted_mean, 4),
                "fuzzy_vs_classic_gap": round(self.fuzzy_vs_classic_gap, 4),
            },
            "axis_weights": {k: round(v, 4) for k, v in self.axis_weights.items()},
            "axes": [ax.to_dict() for ax in self.axes],
            "incoherences": [
                {
                    "name": r.name,
                    "description": r.description,
                    "strength": round(r.strength, 4),
                    "axes_involved": list(r.axes_involved),
                    "severity": r.consequent,
                }
                for r in self.fired_rules
            ],
        }
