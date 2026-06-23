"""Ingestion du corpus dans le graphe de connaissances (Étape 5).

Construit un **PropertyGraphIndex** (LlamaIndex) adossé à Neo4j à partir des
documents de ``data/corpus/``. L'extraction d'entités/relations est guidée par un
schéma aligné sur les ``target_entities`` du référentiel.

Exécution (prérequis) :
    docker compose up -d                 # Neo4j + APOC
    pip install -e ".[graphrag,report]"  # llama-index, neo4j, LLM
    # variables NEO4J_* et clés LLM/embeddings dans .env
    python scripts/build_graph.py

Les imports lourds (llama-index) sont **paresseux** : le package s'installe et se
teste sans l'extra ``graphrag``.
"""

from __future__ import annotations

from pathlib import Path

from maturai.config import CORPUS_DIR, Neo4jConfig

# Types d'entités/relations recherchés (alignés sur le référentiel Gouvernance/Data).
ENTITIES = [
    "CharteIA", "ComiteIA", "AIOfficer", "RegistreRisques", "SystemeIA",
    "EUAIAct", "RGPD", "RisqueLLM", "ShadowAI", "PlanIncident",
    "DataLake", "CatalogueDonnees", "PolitiqueDonnees", "EquipeIA",
    "FormationIA", "BudgetIA", "Document",
]
RELATIONS = [
    "PUBLIE_PAR", "COUVRE", "RESPONSABLE_DE", "INSCRIT_AU", "CLASSIFIE_SELON",
    "CONFORME_A", "MENTIONNE", "RATTACHE_A",
]


def _build_graph_store(config: Neo4jConfig):
    from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

    return Neo4jPropertyGraphStore(
        username=config.user,
        password=config.password,
        url=config.uri,
        database=config.database,
    )


def ingest_corpus(
    corpus_dir: Path = CORPUS_DIR,
    config: Neo4jConfig | None = None,
):
    """Construit (et persiste dans Neo4j) le knowledge graph du corpus.

    Returns:
        L'instance ``PropertyGraphIndex`` construite.

    Raises:
        ImportError: si l'extra ``graphrag`` n'est pas installé.
    """
    config = config or Neo4jConfig()
    try:
        from llama_index.core import PropertyGraphIndex, SimpleDirectoryReader
        from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
    except ImportError as exc:  # pragma: no cover - dépendance optionnelle
        raise ImportError(
            'Graph-RAG requiert : pip install -e ".[graphrag,report]"'
        ) from exc

    documents = SimpleDirectoryReader(
        str(corpus_dir), required_exts=[".md", ".pdf", ".txt"]
    ).load_data()
    graph_store = _build_graph_store(config)

    kg_extractor = SchemaLLMPathExtractor(
        llm=_default_llm(),
        possible_entities=ENTITIES,        # type: ignore[arg-type]
        possible_relations=RELATIONS,      # type: ignore[arg-type]
        strict=False,
    )

    index = PropertyGraphIndex.from_documents(
        documents,
        property_graph_store=graph_store,
        kg_extractors=[kg_extractor],
        embed_model=_default_embed_model(),
        show_progress=True,
    )
    return index


def _default_llm():
    """LLM par défaut pour l'extraction (Anthropic via LlamaIndex)."""
    import os

    from llama_index.llms.anthropic import Anthropic

    return Anthropic(model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"))


def _default_embed_model():
    import os

    from llama_index.embeddings.openai import OpenAIEmbedding

    return OpenAIEmbedding(model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"))
