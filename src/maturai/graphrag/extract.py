"""Extraction de preuves depuis le graphe (Étape 5).

Implémente le contrat :class:`maturai.graphrag.interfaces.EvidenceExtractor` en
interrogeant le ``PropertyGraphIndex`` (Neo4j + LlamaIndex). Pour chaque question :

1. construire une requête à partir du texte de la question et de ses
   ``target_entities`` (déclarées dans le référentiel) ;
2. récupérer le sous-graphe + les passages pertinents (recherche hybride) ;
3. demander au LLM de **mapper** l'évidence sur une **modalité 0..4** de la
   question (parmi les 5 libellés du référentiel), avec extrait justificatif et
   niveau de confiance.

Respecte exactement le contrat du mock : la bascule mock → réel ne change aucun
code aval (réconciliation, scoring). Imports lourds paresseux.
"""

from __future__ import annotations

import json
import re

from maturai.config import Neo4jConfig
from maturai.domain.referential import Referential, ScoredQuestion
from maturai.graphrag.interfaces import EvidenceSuggestion

_EXTRACT_SYS = (
    "Tu analyses des documents internes pour évaluer la maturité IA d'une "
    "organisation. À partir des extraits fournis, tu choisis la modalité (0 à 4) "
    "qui correspond le mieux, parmi les 5 proposées. Tu réponds STRICTEMENT en "
    "JSON : {\"score\": <0-4>, \"confidence\": <0-1>, \"snippet\": \"<extrait cité>\"}. "
    "Si les extraits ne permettent pas de conclure, score le plus probable et "
    "confidence basse."
)


class GraphRagEvidenceExtractor:
    """Extracteur de preuves réel (Graph-RAG)."""

    def __init__(
        self,
        referential: Referential,
        index=None,
        config: Neo4jConfig | None = None,
        *,
        similarity_top_k: int = 5,
    ) -> None:
        self.referential = referential
        self.config = config or Neo4jConfig()
        self.similarity_top_k = similarity_top_k
        self._index = index
        self._questions: dict[str, ScoredQuestion] = {
            q.id: q for q in referential.iter_scored_questions()
        }

    # ------------------------------------------------------------------ #
    def _ensure_index(self):
        if self._index is not None:
            return self._index
        from llama_index.core import PropertyGraphIndex

        from maturai.graphrag.ingest import _build_graph_store, _default_embed_model

        self._index = PropertyGraphIndex.from_existing(
            property_graph_store=_build_graph_store(self.config),
            embed_model=_default_embed_model(),
        )
        return self._index

    def _retrieve(self, question: ScoredQuestion) -> str:
        index = self._ensure_index()
        entities = question.graph_rag.target_entities if question.graph_rag else []
        query = question.text + " " + " ".join(entities)
        retriever = index.as_retriever(similarity_top_k=self.similarity_top_k)
        nodes = retriever.retrieve(query)
        return "\n---\n".join(n.get_content() for n in nodes)

    def _map_to_score(self, question: ScoredQuestion, context: str) -> EvidenceSuggestion | None:
        if not context.strip():
            return None
        from maturai.graphrag.ingest import _default_llm

        levels = "\n".join(f"  {lvl.score}: {lvl.label}" for lvl in question.levels)
        prompt = (
            f"Question : {question.text}\n\nModalités possibles :\n{levels}\n\n"
            f"Extraits documentaires :\n{context}\n\nRéponds en JSON."
        )
        raw = _default_llm().complete(f"{_EXTRACT_SYS}\n\n{prompt}").text
        parsed = _parse_json(raw)
        if parsed is None:
            return None
        score = int(max(0, min(4, parsed.get("score", 0))))
        return EvidenceSuggestion(
            question_id=question.id,
            suggested_score=score,
            confidence=float(max(0.0, min(1.0, parsed.get("confidence", 0.5)))),
            snippet=str(parsed.get("snippet", ""))[:500],
            source_document="graph",
            entities=question.graph_rag.target_entities if question.graph_rag else [],
        )

    # ------------------------------------------------------------------ #
    def suggest_for_question(self, question_id: str) -> list[EvidenceSuggestion]:
        question = self._questions.get(question_id)
        if question is None:
            return []
        context = self._retrieve(question)
        suggestion = self._map_to_score(question, context)
        return [suggestion] if suggestion else []

    def suggest_all(self, question_ids: list[str]) -> dict[str, list[EvidenceSuggestion]]:
        return {qid: self.suggest_for_question(qid) for qid in question_ids}


def _parse_json(raw: str) -> dict | None:
    """Extrait le premier objet JSON d'une réponse LLM (robuste au texte autour)."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
