"""Schémas d'API de l'interface web (requêtes/réponses).

Découple le contrat HTTP des modèles de domaine internes : le front envoie des
réponses simples (``{question_id: score}``) et reçoit le score structuré.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssessRequest(BaseModel):
    """Payload d'évaluation envoyé par le front."""

    client_name: str = "Client"
    sector: str | None = None
    context: dict[str, str] = Field(default_factory=dict)
    answers: dict[str, int] = Field(default_factory=dict)  # {question_id: score 0..4}
    confidences: dict[str, float] = Field(default_factory=dict)  # optionnel
    roi_inputs: dict[str, float | str] = Field(default_factory=dict)


class AssessResponse(BaseModel):
    """Réponse d'évaluation renvoyée au front."""

    score: dict
    roi: dict | None = None
    report_markdown: str
