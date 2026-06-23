"""Construit le graphe de connaissances Graph-RAG depuis le corpus (étape 5).

Prérequis :
    docker compose up -d
    pip install -e ".[graphrag,report]"
    # .env : NEO4J_*, ANTHROPIC_API_KEY, OPENAI_API_KEY (embeddings)

Usage :
    python scripts/build_graph.py
"""

from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from maturai.config import CORPUS_DIR, Neo4jConfig
from maturai.graphrag.ingest import ingest_corpus
from maturai.graphrag.neo4j_client import Neo4jClient


def main() -> None:
    cfg = Neo4jConfig()
    print(f"Connexion Neo4j : {cfg.uri} (db={cfg.database})")
    with Neo4jClient(cfg) as client:
        if not client.ping():
            print("Neo4j injoignable. Lancer : docker compose up -d")
            sys.exit(1)
    print(f"Ingestion du corpus : {CORPUS_DIR}")
    ingest_corpus(CORPUS_DIR, cfg)
    print("Graphe construit. Console Neo4j : http://localhost:7474")


if __name__ == "__main__":
    main()
