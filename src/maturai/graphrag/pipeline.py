"""Réconciliation réponses ↔ preuves : du Graph-RAG vers le score de confiance.

C'est le **chaînon point 5 → point 3** : les preuves extraites des documents
ajustent la *confiance* portée par chaque réponse, qui pilote à son tour la
largeur du TFN à la fuzzification (donc l'incertitude propagée jusqu'au score).

Trois cas par question :

* **corroborée** (preuve ≈ réponse déclarée) → confiance maintenue ou légèrement
  renforcée : on est plus sûr de la réponse ;
* **contredite** (écart preuve/déclaration) → confiance abaissée proportionnellement
  à l'écart : la réponse devient plus incertaine (TFN élargi) et l'écart est
  remonté comme :class:`CoherenceFinding` à valider par les parties prenantes ;
* **non répondue mais preuve disponible** → réponse *suggérée* (``source="graph_rag"``)
  avec la confiance de l'extraction, à valider ensuite.

Ce module fonctionne avec n'importe quel :class:`EvidenceExtractor` (mock ou
Graph-RAG réel) — il est donc testable dès maintenant sans Neo4j.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from maturai.domain.responses import Assessment, QuestionResponse
from maturai.graphrag.interfaces import (
    CoherenceFinding,
    EvidenceExtractor,
    EvidenceSuggestion,
    detect_coherence,
)


@dataclass(frozen=True)
class ReconciliationResult:
    """Résultat de la réconciliation : évaluation enrichie + traces."""

    assessment: Assessment  # copie avec confiances ajustées + réponses suggérées
    findings: list[CoherenceFinding]  # écarts déclaration/preuve à valider
    suggested: list[QuestionResponse] = field(default_factory=list)  # réponses pré-remplies

    @property
    def n_contradicted(self) -> int:
        return len(self.findings)


def _adjusted_confidence(base: float, gap: int) -> float:
    """Confiance ajustée selon l'accord preuve/déclaration.

    * accord parfait (gap 0) : léger renforcement ;
    * écart |gap| : décote linéaire (0,25 par niveau), plancher 0,2.
    """
    if gap == 0:
        return min(1.0, base + 0.1)
    return max(0.2, base * (1.0 - 0.25 * abs(gap)))


def reconcile(
    assessment: Assessment,
    extractor: EvidenceExtractor,
    *,
    tolerance: int = 1,
    fill_unanswered: bool = True,
) -> ReconciliationResult:
    """Confronte les réponses aux preuves et renvoie une évaluation enrichie.

    Args:
        assessment: évaluation déclarée.
        extractor: extracteur de preuves (mock ou Graph-RAG réel).
        tolerance: écart toléré avant de considérer une contradiction.
        fill_unanswered: si vrai, pré-remplit les questions sans réponse à partir
            des preuves disponibles.
    """
    declared = {r.question_id: r for r in assessment.responses}
    asked_ids = list(declared.keys())

    # Preuves pour les questions répondues (réconciliation) + non répondues (pré-remplissage)
    target_ids = set(asked_ids)
    if fill_unanswered:
        target_ids |= {qid for qid in _all_evidence_ids(extractor, asked_ids)}
    evidence = extractor.suggest_all(sorted(target_ids))

    findings = detect_coherence(
        {qid: r.score for qid, r in declared.items()}, evidence, tolerance=tolerance
    )

    new_responses: list[QuestionResponse] = []
    for qid, resp in declared.items():
        best = _best_evidence(evidence.get(qid, []))
        if best is None:
            new_responses.append(resp)
            continue
        gap = best.suggested_score - resp.score
        new_responses.append(
            resp.model_copy(
                update={
                    "confidence": _adjusted_confidence(resp.confidence, gap),
                    "source": "reconciled",
                }
            )
        )

    suggested: list[QuestionResponse] = []
    if fill_unanswered:
        for qid, sugg_list in evidence.items():
            if qid in declared:
                continue
            best = _best_evidence(sugg_list)
            if best is None:
                continue
            suggested.append(
                QuestionResponse(
                    question_id=qid,
                    score=best.suggested_score,
                    confidence=best.confidence,
                    source="graph_rag",
                )
            )

    enriched = assessment.model_copy(update={"responses": new_responses + suggested})
    return ReconciliationResult(assessment=enriched, findings=findings, suggested=suggested)


def _best_evidence(suggestions: list[EvidenceSuggestion]) -> EvidenceSuggestion | None:
    return max(suggestions, key=lambda s: s.confidence) if suggestions else None


def _all_evidence_ids(extractor: EvidenceExtractor, asked_ids: list[str]) -> list[str]:
    """Heuristique : un extracteur mock expose ses fixtures ; sinon on se limite
    aux questions posées (le Graph-RAG réel sera interrogé question par question)."""
    fixtures = getattr(extractor, "_fixtures", None)
    if isinstance(fixtures, dict):
        return list(fixtures.keys())
    return asked_ids
