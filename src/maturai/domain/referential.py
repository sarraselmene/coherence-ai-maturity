"""Modèles de domaine du référentiel (typés, validés par pydantic).

Ces classes sont le miroir Python de ``data/referential/questions.json``. Elles
fournissent une API navigable (axes → sous-domaines → questions) et garantissent,
dès le chargement, qu'aucune brique aval ne manipule un référentiel incohérent.

La validation *structurelle* (forme du JSON) est faite par jsonschema ; la
validation *sémantique* (5 niveaux 0..4 strictement croissants, identifiants
uniques, sources connues…) est faite ici et dans :mod:`maturai.referential.validators`. 

Pydantic fait automatiquement :

vérification des types
validation
création des objets Python

"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Layer = Literal["generic", "ai_specific"]


class Scale(BaseModel):
    internal_min: int
    internal_max: int
    presented_min: int | None = None
    presented_max: int | None = None
    model: str | None = None
    note: str | None = None


class ReferentialSource(BaseModel):
    label: str
    role: str
    type: str


class Weighting(BaseModel):
    method: str
    note: str | None = None
    fallback_axis_weights: dict[str, float]


class Meta(BaseModel):
    name: str
    version: str
    date: str | None = None
    language: str = "fr"
    scale: Scale
    level_labels: dict[str, str]
    referential_sources: dict[str, ReferentialSource]
    weighting: Weighting


class GraphRagHint(BaseModel):
    hint: str | None = None
    target_entities: list[str] = Field(default_factory=list)


class Level(BaseModel):
    score: int
    label: str

    @field_validator("score")
    @classmethod
    def _score_range(cls, v: int) -> int:
        if not 0 <= v <= 4:
            raise ValueError("score de niveau hors [0, 4]")
        return v


class QuestionTraceability(BaseModel):
    """Traçabilité d'une question vers ses sources (champ ``referential``)."""

    sources: list[str]
    justification: str


class ScoredQuestion(BaseModel):
    id: str
    weight: float = 1.0
    layer: Layer
    text: str
    levels: list[Level]
    referential: QuestionTraceability
    graph_rag: GraphRagHint | None = None

    @field_validator("levels")
    @classmethod
    def _five_increasing_levels(cls, v: list[Level]) -> list[Level]:
        scores = [lvl.score for lvl in v]
        if scores != [0, 1, 2, 3, 4]:
            raise ValueError(f"les 5 niveaux doivent être 0..4 dans l'ordre, reçu {scores}")
        return v


class SubDomain(BaseModel):
    id: str
    name: str
    weight: float = 1.0
    questions: list[ScoredQuestion]


class Axis(BaseModel):
    id: str
    code: str | None = None
    name: str
    weight: float
    anchor: list[str] = Field(default_factory=list)
    subdomains: list[SubDomain]

    def iter_questions(self) -> list[ScoredQuestion]:
        return [q for sd in self.subdomains for q in sd.questions]


class ContextQuestion(BaseModel):
    id: str
    field: str | None = None
    text: str
    type: str
    options: list[str] = Field(default_factory=list)
    usage: str | None = None
    graph_rag: GraphRagHint | None = None


class ContextSection(BaseModel):
    id: str
    name: str | None = None
    scored: Literal[False] = False
    questions: list[ContextQuestion]


class ROIInput(BaseModel):
    id: str
    field: str
    type: str
    unit: str | None = None
    options: list[str] = Field(default_factory=list)
    text: str
    usage: str
    graph_rag: GraphRagHint | None = None


class ROIModule(BaseModel):
    id: str
    name: str | None = None
    scored: Literal[False] = False
    note: str | None = None
    inputs: list[ROIInput]


class Referential(BaseModel):
    """Racine du référentiel."""

    meta: Meta
    context_section: ContextSection
    axes: list[Axis]
    roi_module: ROIModule

    # ----------------------------- navigation ----------------------------- #
    def axis(self, axis_id: str) -> Axis:
        for ax in self.axes:
            if ax.id == axis_id:
                return ax
        raise KeyError(f"axe inconnu : {axis_id!r}")

    def iter_scored_questions(self) -> list[ScoredQuestion]:
        return [q for ax in self.axes for q in ax.iter_questions()]

    def question_ids(self) -> list[str]:
        return [q.id for q in self.iter_scored_questions()]

    def axis_weights(self) -> dict[str, float]:
        """Poids d'axes déclarés dans le JSON (valeurs de repli)."""
        return {ax.id: ax.weight for ax in self.axes}

    @property
    def n_scored_questions(self) -> int:
        return len(self.iter_scored_questions())
