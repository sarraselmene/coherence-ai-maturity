"""Fonctions d'appartenance triangulaires sur les 5 niveaux de maturité.

L'univers des scores est ``[0, 4]``. On y définit 5 ensembles flous, un par
niveau CMMI, dont les sommets coïncident avec les entiers 0..4 :

    niveau 0 (Initial)   : (0, 0, 1)   — épaule gauche
    niveau 1 (Émergent)  : (0, 1, 2)
    niveau 2 (Défini)    : (1, 2, 3)
    niveau 3 (Géré)      : (2, 3, 4)
    niveau 4 (Optimisé)  : (3, 4, 4)   — épaule droite

Ce recouvrement (chaque point appartient à au plus deux niveaux adjacents)
matérialise l'idée centrale du sujet : *une réponse réelle se situe rarement
strictement à un niveau, mais entre deux niveaux adjacents*. Un score de 2,4
appartient ainsi à « Défini » (degré 0,6) et « Géré » (degré 0,4).

Ces MF servent (1) à interpréter un score continu en profil d'appartenance pour
le rapport, et (2) d'ensembles linguistiques pour l'inférence Mamdani inter-axes.
"""

from __future__ import annotations

import numpy as np

LEVEL_NAMES: tuple[str, ...] = ("Initial", "Émergent", "Défini", "Géré", "Optimisé")


def trimf(x: float, a: float, b: float, c: float) -> float:
    """Fonction d'appartenance triangulaire (équivalent ``skfuzzy.trimf``).

    Gère les épaules (``a == b`` ou ``b == c``) sans division par zéro.
    """
    if a == b == c:
        return 1.0 if x == a else 0.0
    if x < a or x > c:
        return 0.0
    left = 1.0 if b <= a else (x - a) / (b - a)
    right = 1.0 if c <= b else (c - x) / (c - b)
    return max(min(left, right), 0.0)


# Sommets des 5 MF de niveau sur [0, 4].
_LEVEL_VERTICES: tuple[tuple[float, float, float], ...] = (
    (0.0, 0.0, 1.0),
    (0.0, 1.0, 2.0),
    (1.0, 2.0, 3.0),
    (2.0, 3.0, 4.0),
    (3.0, 4.0, 4.0),
)


def level_vertices() -> tuple[tuple[float, float, float], ...]:
    """Renvoie les sommets ``(a, b, c)`` des 5 MF de niveau."""
    return _LEVEL_VERTICES


def membership_vector(x: float) -> np.ndarray:
    """Vecteur des 5 degrés d'appartenance de ``x`` aux niveaux 0..4."""
    return np.array([trimf(x, *v) for v in _LEVEL_VERTICES])


def level_degrees(x: float) -> dict[str, float]:
    """Profil d'appartenance lisible : ``{nom_niveau: degré}`` (degrés > 0)."""
    vec = membership_vector(x)
    return {LEVEL_NAMES[i]: float(d) for i, d in enumerate(vec) if d > 1e-9}


def dominant_level(x: float) -> int:
    """Niveau (0..4) de plus forte appartenance pour ``x``."""
    return int(np.argmax(membership_vector(x)))
