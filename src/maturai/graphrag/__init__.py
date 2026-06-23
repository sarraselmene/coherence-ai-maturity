"""Pipeline Graph-RAG (Étape 5 / enrichissement point 5).

Exporte les contrats et l'extracteur mock (utilisables immédiatement). Les
implémentations réelles (Neo4j + LlamaIndex) sont dans ``ingest`` / ``extract``.
"""

from maturai.graphrag.interfaces import (
    CoherenceFinding,
    EvidenceExtractor,
    EvidenceSuggestion,
    detect_coherence,
)
from maturai.graphrag.mock import MockEvidenceExtractor
from maturai.graphrag.pipeline import ReconciliationResult, reconcile

__all__ = [
    "EvidenceSuggestion",
    "CoherenceFinding",
    "EvidenceExtractor",
    "detect_coherence",
    "MockEvidenceExtractor",
    "reconcile",
    "ReconciliationResult",
]
