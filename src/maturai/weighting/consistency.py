"""Contrôle de cohérence d'une matrice de comparaisons par paires (Saaty).

Une matrice de jugements n'a de valeur que si elle est *cohérente* : si A est 2×
plus important que B et B 3× plus que C, alors A doit être ~6× plus que C. Saaty
quantifie ce respect par le **ratio de cohérence** (CR). Au-delà de 0,10, les
jugements sont jugés trop incohérents et doivent être révisés.

On le calcule sur la matrice **crisp** (avant fuzzification) : c'est la pratique
courante, la fuzzification n'ajoutant qu'une tolérance autour des jugements.
"""

from __future__ import annotations

import numpy as np

# Indices d'incohérence aléatoire de Saaty (RI), indexés par la taille n.
_RANDOM_INDEX = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}


def principal_eigen(matrix: np.ndarray) -> tuple[float, np.ndarray]:
    """Valeur propre principale ``lambda_max`` et vecteur de priorité associé.

    Le vecteur propre est normalisé pour sommer à 1 (poids de priorité).
    """
    eigvals, eigvecs = np.linalg.eig(matrix)
    idx = int(np.argmax(eigvals.real))
    lambda_max = float(eigvals[idx].real)
    vec = np.abs(eigvecs[:, idx].real)
    vec = vec / vec.sum()
    return lambda_max, vec


def consistency_ratio(matrix: np.ndarray) -> float:
    """Ratio de cohérence CR = CI / RI.

    ``CI = (lambda_max - n) / (n - 1)``. Renvoie 0 pour n <= 2 (toujours cohérent).
    """
    n = matrix.shape[0]
    if n <= 2:
        return 0.0
    lambda_max, _ = principal_eigen(matrix)
    ci = (lambda_max - n) / (n - 1)
    ri = _RANDOM_INDEX.get(n)
    if ri is None or ri == 0.0:  # pragma: no cover - n hors table
        return 0.0
    return ci / ri


def is_consistent(matrix: np.ndarray, threshold: float = 0.10) -> bool:
    return consistency_ratio(matrix) <= threshold
