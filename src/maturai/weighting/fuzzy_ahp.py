"""Fuzzy AHP — pondération inter-axes par comparaisons par paires.

Implémente la méthode d'**analyse des étendues de Chang (1996)**, la plus citée
pour le Fuzzy AHP :

1. les jugements de Saaty (crisp) sont **fuzzifiés** en nombres flous
   triangulaires (TFN) — un jugement « 3 » devient ``(2, 3, 4)``, traduisant
   l'imprécision de l'expert ;
2. on calcule l'**étendue synthétique floue** de chaque axe
   ``S_i = (Σ_j M_ij) ⊗ (Σ_i Σ_j M_ij)^{-1}`` ;
3. on évalue le **degré de possibilité** ``V(S_i ≥ S_k)`` entre étendues ;
4. les poids résultent du minimum de ces degrés, normalisés.

Avantage vs AHP classique : les poids ne reposent pas sur des jugements supposés
exacts mais sur des plages, ce qui est plus honnête et **traçable** — réponse
directe à la critique « pondération arbitraire » des grilles propriétaires.

La cohérence des jugements est vérifiée en amont (cf.
:mod:`maturai.weighting.consistency`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from maturai.config import AHP_PAIRWISE_PATH
from maturai.domain.fuzzy_number import TriangularFuzzyNumber as TFN
from maturai.weighting.consistency import consistency_ratio


def saaty_to_tfn(value: float) -> TFN:
    """Fuzzifie un jugement de Saaty crisp en TFN (convention standard).

    * ``1``          -> ``(1, 1, 1)``
    * ``x`` (2..9)   -> ``(x-1, x, x+1)`` (borné en bas à 1)
    * ``1/x``        -> ``(1/(x+1), 1/x, 1/(x-1))``
    """
    if abs(value - 1.0) < 1e-9:
        return TFN(1.0, 1.0, 1.0)
    if value > 1.0:
        return TFN(max(1.0, value - 1.0), value, value + 1.0)
    # réciproque : value = 1/x  ->  x = 1/value
    x = 1.0 / value
    return TFN(1.0 / (x + 1.0), 1.0 / x, 1.0 / max(1.0, x - 1.0))


@dataclass(frozen=True)
class FuzzyAHPResult:
    """Résultat d'une pondération par Fuzzy AHP.

    Deux jeux de poids sont fournis :

    * ``weights`` (faisant foi) : centroïdes des étendues synthétiques floues,
      normalisés. Toujours strictement positifs — robuste pour l'agrégation.
    * ``chang_weights`` : poids par degré de possibilité (méthode originale de
      Chang). Conservés pour la discussion du mémoire ; peuvent contenir des
      zéros (limite connue de la méthode), d'où leur non-usage par défaut.
    """

    items: list[str]
    weights: dict[str, float]  # centroïdes normalisés (faisant foi)
    chang_weights: dict[str, float]  # degrés de possibilité (Chang, comparatif)
    synthetic_extents: dict[str, TFN]  # étendues synthétiques floues S_i
    consistency_ratio: float
    is_consistent: bool

    def as_vector(self) -> np.ndarray:
        return np.array([self.weights[i] for i in self.items])


def _degree_of_possibility(m2: TFN, m1: TFN) -> float:
    """Degré de possibilité ``V(M2 >= M1)`` (Chang)."""
    if m2.m >= m1.m:
        return 1.0
    if m1.a >= m2.b:
        return 0.0
    # intersection des deux pentes
    denom = (m2.m - m2.b) - (m1.m - m1.a)
    if abs(denom) < 1e-12:  # pragma: no cover - cas dégénéré
        return 0.0
    return (m1.a - m2.b) / denom


def fuzzy_ahp_weights(
    matrix: list[list[float]] | np.ndarray,
    items: list[str],
    *,
    consistency_threshold: float = 0.10,
) -> FuzzyAHPResult:
    """Calcule les poids par l'analyse des étendues de Chang.

    Args:
        matrix: matrice carrée de jugements de Saaty (crisp, réciproque).
        items: noms des éléments comparés (ordre = lignes/colonnes).
        consistency_threshold: seuil de CR au-delà duquel on signale l'incohérence.
    """
    mat = np.asarray(matrix, dtype=float)
    n = mat.shape[0]
    if mat.shape != (n, n):
        raise ValueError("la matrice de comparaison doit être carrée")
    if len(items) != n:
        raise ValueError("items et matrice de tailles incompatibles")

    cr = consistency_ratio(mat)

    # 1. Fuzzification des jugements
    fuzzy: list[list[TFN]] = [[saaty_to_tfn(mat[i, j]) for j in range(n)] for i in range(n)]

    # 2. Étendues synthétiques floues S_i = rowSum_i ⊗ (totalSum)^-1
    row_sums = [
        TFN(
            sum(fuzzy[i][j].a for j in range(n)),
            sum(fuzzy[i][j].m for j in range(n)),
            sum(fuzzy[i][j].b for j in range(n)),
        )
        for i in range(n)
    ]
    total = TFN(
        sum(rs.a for rs in row_sums),
        sum(rs.m for rs in row_sums),
        sum(rs.b for rs in row_sums),
    )
    # inverse d'une somme floue : (1/u, 1/m, 1/l)
    total_inv = TFN(1.0 / total.b, 1.0 / total.m, 1.0 / total.a)
    extents = [rs * total_inv for rs in row_sums]

    # 3a. Poids faisant foi : centroïdes des étendues, normalisés (robuste).
    centroids = np.array([e.defuzzify() for e in extents])
    centroids = np.maximum(centroids, 0.0)
    weights_vec = centroids / centroids.sum() if centroids.sum() > 0 else np.ones(n) / n

    # 3b. Poids de Chang (degré de possibilité), pour comparaison.
    d_prime = np.zeros(n)
    for i in range(n):
        degrees = [_degree_of_possibility(extents[i], extents[k]) for k in range(n) if k != i]
        d_prime[i] = min(degrees) if degrees else 1.0
    chang_vec = d_prime / d_prime.sum() if d_prime.sum() > 0 else np.ones(n) / n

    weights = {items[i]: float(weights_vec[i]) for i in range(n)}
    chang = {items[i]: float(chang_vec[i]) for i in range(n)}
    synthetic = {items[i]: extents[i] for i in range(n)}
    return FuzzyAHPResult(
        items=list(items),
        weights=weights,
        chang_weights=chang,
        synthetic_extents=synthetic,
        consistency_ratio=cr,
        is_consistent=cr <= consistency_threshold,
    )


def load_axis_weights(path: Path | str = AHP_PAIRWISE_PATH) -> FuzzyAHPResult:
    """Charge la matrice par paires inter-axes et calcule les poids."""
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    items = data["axes_order"]
    matrix = data["matrix"]
    threshold = data.get("meta", {}).get("consistency_threshold", 0.10)
    return fuzzy_ahp_weights(matrix, items, consistency_threshold=threshold)
