"""Catalogue de KPI de suivi par axe (sortie couche 4 du système).

Chaque axe est associé à des indicateurs de pilotage que le rapport LLM
contextualise et priorise selon le score obtenu. Les définir en dur (plutôt que
de les laisser inventer par le LLM) garantit leur **pertinence et leur
reproductibilité** : le LLM choisit et formule, il n'improvise pas la métrique.
"""

from __future__ import annotations

KPI_CATALOG: dict[str, list[str]] = {
    "strategy": [
        "% de projets IA rattachés à un objectif métier chiffré",
        "Part du budget IA dans le budget d'investissement total",
        "Nombre de cas d'usage IA priorisés au COMEX",
    ],
    "data": [
        "% de jeux de données critiques sous monitoring qualité",
        "Couverture du catalogue de données (% des domaines)",
        "% de modèles IA dont le lineage des données est documenté",
    ],
    "talents": [
        "Nombre d'ETP formés à l'IA / effectif total",
        "Taux de couverture des rôles IA clés (pourvus vs cibles)",
        "Nombre d'expérimentations IA lancées par trimestre",
    ],
    "technology": [
        "Ratio modèles en production / modèles en pilote",
        "% de modèles couverts par le MLOps (versionning + monitoring)",
        "Disponibilité de l'infrastructure IA (SLA)",
    ],
    "governance": [
        "% de systèmes IA classifiés selon l'EU AI Act",
        "% de systèmes à haut risque disposant d'une documentation technique conforme",
        "Délai moyen de traitement d'un incident IA",
        "% de projets IA passés par une revue RGPD",
    ],
}


def kpis_for_axis(axis_id: str) -> list[str]:
    return KPI_CATALOG.get(axis_id, [])
