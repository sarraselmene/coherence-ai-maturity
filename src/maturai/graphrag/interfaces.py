"""Contrats du pipeline Graph-RAG (Étape 5 / enrichissement point 5).

On définit ici les **interfaces** (au sens ``typing.Protocol``) avant toute
implémentation, pour deux raisons :

1. le moteur de scoring et le questionnaire dépendent du *contrat* d'extraction
   de preuves, pas de Neo4j/LlamaIndex — on peut donc développer et tester tout
   le reste avec un :class:`maturai.graphrag.mock.MockEvidenceExtractor` ;
2. la **détection d'incohérences** entre réponse déclarée et preuve extraite
   alimente le *score de confiance* qui module la fuzzification (point 5 → point 3).

Le contrat central : à partir d'une question, l'extracteur renvoie zéro ou
plusieurs :class:`EvidenceSuggestion` (score suggéré + extrait justificatif +
provenance + confiance).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class EvidenceSuggestion:
    """Preuve extraite d'un document, suggérant une réponse à une question."""

    question_id: str
    suggested_score: int  # 0..4
    confidence: float  # [0,1] : fiabilité de l'extraction
    snippet: str  # extrait textuel justificatif
    source_document: str  # provenance (nom de fichier / nœud du graphe)
    entities: list[str] = field(default_factory=list)  # entités du graphe ayant matché

    def agrees_with(self, declared_score: int, tolerance: int = 1) -> bool:
        """Vrai si la preuve corrobore la réponse déclarée (à ``tolerance`` près)."""
        return abs(self.suggested_score - declared_score) <= tolerance


@dataclass(frozen=True)
class CoherenceFinding:
    """Écart détecté entre une réponse déclarée et la preuve documentaire."""

    question_id: str
    declared_score: int
    evidence_score: int
    gap: int
    snippet: str
    source_document: str


@runtime_checkable
class EvidenceExtractor(Protocol):
    """Contrat d'un extracteur de preuves (mock ou Graph-RAG réel)."""

    def suggest_for_question(self, question_id: str) -> list[EvidenceSuggestion]:
        """Renvoie les preuves extraites pour une question donnée."""
        ...

    def suggest_all(self, question_ids: list[str]) -> dict[str, list[EvidenceSuggestion]]:
        """Renvoie les preuves pour un lot de questions."""
        ...


def detect_coherence(
    declared: dict[str, int],
    evidence: dict[str, list[EvidenceSuggestion]],
    *,
    tolerance: int = 1,
) -> list[CoherenceFinding]:
    """Compare réponses déclarées et preuves ; remonte les écarts significatifs.

    Sert (1) à alerter les parties prenantes lors de la validation des réponses
    et (2) à abaisser la confiance des réponses non corroborées, ce qui élargit
    leur TFN dans le moteur (propagation d'incertitude).
    """
    findings: list[CoherenceFinding] = []
    for qid, declared_score in declared.items():
        suggestions = evidence.get(qid, [])
        if not suggestions:
            continue
        # preuve la plus confiante
        best = max(suggestions, key=lambda s: s.confidence)
        gap = best.suggested_score - declared_score
        if abs(gap) > tolerance:
            findings.append(
                CoherenceFinding(
                    question_id=qid,
                    declared_score=declared_score,
                    evidence_score=best.suggested_score,
                    gap=gap,
                    snippet=best.snippet,
                    source_document=best.source_document,
                )
            )
    return findings
