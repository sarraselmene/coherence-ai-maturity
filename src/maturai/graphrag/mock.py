"""Extracteur de preuves *mock* — permet de tourner de bout en bout sans Neo4j.

Implémente le contrat :class:`maturai.graphrag.interfaces.EvidenceExtractor` en
renvoyant des suggestions déterministes définies en dur. Cela débloque :

* le développement de la réconciliation réponse/preuve et du score de confiance ;
* les tests d'intégration du questionnaire pré-rempli ;
* la démonstration end-to-end avant l'installation du vrai Graph-RAG (étape 5).

Le vrai extracteur (:mod:`maturai.graphrag.extract`) implémentera le **même
contrat** : aucun code aval ne changera lors de la bascule.
"""

from __future__ import annotations

from maturai.graphrag.interfaces import EvidenceSuggestion


class MockEvidenceExtractor:
    """Extracteur déterministe pour tests/démo."""

    def __init__(self, fixtures: dict[str, list[EvidenceSuggestion]] | None = None) -> None:
        self._fixtures = fixtures or _DEFAULT_FIXTURES

    def suggest_for_question(self, question_id: str) -> list[EvidenceSuggestion]:
        return self._fixtures.get(question_id, [])

    def suggest_all(self, question_ids: list[str]) -> dict[str, list[EvidenceSuggestion]]:
        return {qid: self.suggest_for_question(qid) for qid in question_ids}


# Quelques preuves fictives cohérentes avec le corpus prévu (charte IA, audit…).
_DEFAULT_FIXTURES: dict[str, list[EvidenceSuggestion]] = {
    "Q28": [
        EvidenceSuggestion(
            question_id="Q28",
            suggested_score=4,
            confidence=0.9,
            snippet=(
                "La Charte d'éthique IA v2.1 est publiée sur l'intranet et "
                "accessible à tous les collaborateurs."
            ),
            source_document="charte_ia.pdf",
            entities=["Charte IA", "éthique IA"],
        )
    ],
    "Q29": [
        EvidenceSuggestion(
            question_id="Q29",
            suggested_score=2,
            confidence=0.75,
            snippet="Un tableau Excel recense quelques risques IA, sans mise à jour régulière.",
            source_document="rapport_audit_2025.pdf",
            entities=["registre risques IA"],
        )
    ],
    "Q35": [
        EvidenceSuggestion(
            question_id="Q35",
            suggested_score=1,
            confidence=0.8,
            snippet=(
                "Le rapport note une connaissance de l'EU AI Act mais aucune "
                "classification formelle des systèmes."
            ),
            source_document="rapport_audit_2025.pdf",
            entities=["EU AI Act", "classification risque IA"],
        )
    ],
}
