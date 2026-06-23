"""Modèles des réponses collectées et du contexte client.

Une évaluation (``Assessment``) regroupe :

* le **contexte** (secteur, taille…) qui pilote la contextualisation du rapport ;
* les **réponses notées** (questions Q7..Q37 + bis), chacune sur ``[0, 4]`` ;
* les **variables ROI** factuelles (Q38..Q43).

Chaque réponse notée peut porter une **confiance** dans ``[0, 1]`` (par défaut
1.0). Cette confiance — qui sera notamment alimentée par l'accord entre la
réponse déclarée et la preuve extraite par le Graph-RAG (étape 5) — module la
largeur de l'incertitude lors de la fuzzification (cf.
:mod:`maturai.scoring.fuzzification`).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QuestionResponse(BaseModel):
    """Réponse à une question notée."""

    question_id: str
    score: int = Field(..., description="Modalité choisie sur [0, 4]")
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confiance dans la réponse (1 = certaine). Alimentée par le Graph-RAG.",
    )
    source: str = Field(
        "stakeholder",
        description="Origine : 'stakeholder' (déclaratif) | 'graph_rag' (suggéré) | 'reconciled'.",
    )

    @field_validator("score")
    @classmethod
    def _score_range(cls, v: int) -> int:
        if not 0 <= v <= 4:
            raise ValueError("score de réponse hors [0, 4]")
        return v


class ClientContext(BaseModel):
    """Contexte client (section 0, hors scoring)."""

    sector: str | None = None
    region: str | None = None
    headcount: str | None = None
    revenue: str | None = None
    role: str | None = None
    department: str | None = None


class ROIInputs(BaseModel):
    """Variables factuelles du module ROI (Q38..Q43)."""

    n_automatable_tasks: float = 0.0
    hours_per_week: float = 0.0
    cost_per_fte: float = 0.0
    measured_gains: str | None = None  # "Oui avec métriques" | "Estimés" | "Non mesurés"
    ai_budget: float = 0.0
    risk_cost: str | None = None  # "Oui chiffré" | "Estimation grossière" | "Non"


class Assessment(BaseModel):
    """Une évaluation complète d'une organisation."""

    client_name: str = "Client anonyme"
    context: ClientContext = Field(default_factory=ClientContext)
    responses: list[QuestionResponse] = Field(default_factory=list)
    roi_inputs: ROIInputs = Field(default_factory=ROIInputs)

    def responses_by_id(self) -> dict[str, QuestionResponse]:
        return {r.question_id: r for r in self.responses}
