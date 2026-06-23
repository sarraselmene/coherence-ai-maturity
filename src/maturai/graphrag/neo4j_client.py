"""Client Neo4j (Graph-RAG, étape 5).

Encapsule la connexion au graphe de connaissances. L'import du driver ``neo4j``
est **paresseux** : le package s'installe et se teste sans la dépendance
``graphrag``. Le client n'est instancié qu'au moment de l'ingestion ou de
l'extraction réelle.

Configuration via :class:`maturai.config.Neo4jConfig` (variables d'environnement
``NEO4J_*``). Lancer la base avec ``docker compose up -d``.
"""

from __future__ import annotations

from typing import Any

from maturai.config import Neo4jConfig


class Neo4jClient:
    """Connexion fine au-dessus du driver officiel ``neo4j``."""

    def __init__(self, config: Neo4jConfig | None = None) -> None:
        self.config = config or Neo4jConfig()
        self._driver = None

    def connect(self) -> None:
        """Ouvre le driver (import paresseux de ``neo4j``)."""
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:  # pragma: no cover - dépendance optionnelle
            raise ImportError(
                "Le client Neo4j requiert l'extra 'graphrag' : pip install -e \".[graphrag]\""
            ) from exc
        self._driver = GraphDatabase.driver(
            self.config.uri, auth=(self.config.user, self.config.password)
        )

    def ping(self) -> bool:
        """Vérifie la connectivité (``RETURN 1``)."""
        if self._driver is None:
            self.connect()
        assert self._driver is not None
        with self._driver.session(database=self.config.database) as session:
            return session.run("RETURN 1 AS ok").single()["ok"] == 1

    def run(self, cypher: str, **params: Any) -> list[dict]:
        """Exécute une requête Cypher et renvoie les enregistrements."""
        if self._driver is None:
            self.connect()
        assert self._driver is not None
        with self._driver.session(database=self.config.database) as session:
            return [dict(record) for record in session.run(cypher, **params)]

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> Neo4jClient:
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
