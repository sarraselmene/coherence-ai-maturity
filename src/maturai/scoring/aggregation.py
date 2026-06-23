"""Agrégation hiérarchique floue : questions → sous-domaines → axes → global.

L'agrégation remonte la hiérarchie du référentiel par **moyenne pondérée floue**
(cf. :func:`maturai.domain.fuzzy_number.fuzzy_weighted_average`) :

    score(sous-domaine) = Σ w_q · TFN_q / Σ w_q
    score(axe)          = Σ w_sd · TFN_sd / Σ w_sd
    score(global)       = Σ w_axe · TFN_axe / Σ w_axe

Propriété clé : contrairement à une moyenne arithmétique classique qui écrase
l'information, l'opérateur flou **propage l'incertitude** — la largeur du TFN
résultant reflète l'incertitude combinée des composantes. C'est ce qui distingue
le moteur d'un scoring linéaire (argument central du mémoire).

Les poids d'axes proviennent du Fuzzy AHP ; les poids de sous-domaines et de
questions du référentiel (égaux par défaut). Tous peuvent être crisp ou flous.
"""

from __future__ import annotations

from maturai.domain.fuzzy_number import TriangularFuzzyNumber as TFN
from maturai.domain.fuzzy_number import fuzzy_weighted_average


def aggregate(
    values: list[TFN],
    weights: list[float] | list[TFN],
) -> TFN:
    """Moyenne pondérée floue d'un niveau de la hiérarchie."""
    return fuzzy_weighted_average(values, weights)


def aggregate_uniform(values: list[TFN]) -> TFN:
    """Agrégation à poids égaux (cas par défaut sans pondération spécifique)."""
    return fuzzy_weighted_average(values, [1.0] * len(values))
