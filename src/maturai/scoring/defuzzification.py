"""Défuzzification : ensemble flou → valeur crisp interprétable.

Deux usages dans le moteur :

* **TFN → crisp** : centroïde du triangle ``(a + m + b) / 3`` (délégué à
  :meth:`TriangularFuzzyNumber.defuzzify`). C'est la valeur de score présentée.
* **MF échantillonnée → crisp** : centroïde d'une fonction d'appartenance
  quelconque (sortie agrégée d'un système d'inférence Mamdani), calculé par
  quadrature sur un échantillonnage de l'univers.

On retient partout le **centroïde** (centre de gravité) : c'est la méthode de
défuzzification la plus répandue et la plus stable, et l'employer de bout en
bout garantit la cohérence interne des scores.
"""

from __future__ import annotations

import numpy as np

from maturai.domain.fuzzy_number import TriangularFuzzyNumber as TFN


def centroid_tfn(tfn: TFN) -> float:
    """Centroïde d'un TFN."""
    return tfn.defuzzify()


def centroid_of_samples(x: np.ndarray, mu: np.ndarray) -> float:
    """Centroïde d'une MF échantillonnée : ``Σ x·mu / Σ mu``.

    Si l'aire est nulle (aucune règle activée), renvoie le milieu de l'univers
    par convention neutre.
    """
    area = float(mu.sum())
    if area < 1e-12:
        return float((x[0] + x[-1]) / 2.0)
    return float((x * mu).sum() / area)
