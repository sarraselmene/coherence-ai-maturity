"""Nombre flou triangulaire (Triangular Fuzzy Number, TFN).

Le TFN est la structure de données qui porte l'**incertitude bout en bout** du
moteur (feuille de route, point 3). Un TFN ``(a, m, b)`` avec ``a <= m <= b``
représente une grandeur dont :

* ``m`` est la valeur la plus plausible (le *mode*) ;
* ``[a, b]`` est le *support* (les bornes pessimiste/optimiste) ;
* la fonction d'appartenance est triangulaire : 0 en ``a`` et ``b``, 1 en ``m``.

Pourquoi triangulaire plutôt que gaussien ? (1) Deux paramètres de forme
suffisent et restent interprétables par un métier ; (2) l'arithmétique floue
sur les TFN admet des formes fermées simples ; (3) c'est la forme dominante
dans la littérature des modèles de maturité flous et du Fuzzy AHP (Chang).

Toutes les opérations supposent des grandeurs **positives** (scores et poids
sont >= 0), ce qui rend l'arithmétique de multiplication/division exacte sur
les bornes. Les fonctions lèvent une erreur si cette hypothèse est violée, afin
de ne jamais propager silencieusement un résultat faux.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

_TOL = 1e-9


@dataclass(frozen=True, slots=True)
class TriangularFuzzyNumber:
    """Nombre flou triangulaire ``(a, m, b)`` avec ``a <= m <= b``."""

    a: float  # borne inférieure du support (pessimiste)
    m: float  # mode (valeur la plus plausible)
    b: float  # borne supérieure du support (optimiste)

    def __post_init__(self) -> None:
        if not (self.a <= self.m + _TOL and self.m <= self.b + _TOL):
            raise ValueError(
                f"TFN invalide : exige a <= m <= b, reçu ({self.a}, {self.m}, {self.b})"
            )

    # ------------------------------------------------------------------ #
    # Constructeurs
    # ------------------------------------------------------------------ #
    @classmethod
    def crisp(cls, x: float) -> TriangularFuzzyNumber:
        """TFN dégénéré (sans incertitude) : ``(x, x, x)``."""
        return cls(x, x, x)

    @classmethod
    def symmetric(cls, center: float, spread: float) -> TriangularFuzzyNumber:
        """TFN symétrique de centre ``center`` et demi-largeur ``spread``."""
        if spread < 0:
            raise ValueError("spread doit être >= 0")
        return cls(center - spread, center, center + spread)

    # ------------------------------------------------------------------ #
    # Propriétés
    # ------------------------------------------------------------------ #
    @property
    def is_crisp(self) -> bool:
        return abs(self.b - self.a) < _TOL

    @property
    def width(self) -> float:
        """Largeur du support ``b - a`` : mesure scalaire de l'incertitude."""
        return self.b - self.a

    def defuzzify(self) -> float:
        """Défuzzification par **centroïde** d'un triangle : ``(a + m + b) / 3``.

        C'est la méthode retenue dans tout le moteur (cohérence avec la
        défuzzification Mamdani, cf. :mod:`maturai.scoring.defuzzification`).
        """
        return (self.a + self.m + self.b) / 3.0

    def membership(self, x: float) -> float:
        """Degré d'appartenance ``mu(x)`` dans ``[0, 1]``."""
        if x <= self.a or x >= self.b:
            return 0.0
        if abs(x - self.m) < _TOL:
            return 1.0
        if x < self.m:
            return (x - self.a) / (self.m - self.a)
        return (self.b - x) / (self.b - self.m)

    def alpha_cut(self, alpha: float) -> tuple[float, float]:
        """Coupe de niveau ``alpha`` : intervalle ``[a_alpha, b_alpha]``.

        Sert à la propagation d'incertitude par intervalles et au calcul
        d'intervalles de crédibilité (cf. moteur de scoring).
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError("alpha doit être dans [0, 1]")
        lo = self.a + alpha * (self.m - self.a)
        hi = self.b - alpha * (self.b - self.m)
        return (lo, hi)

    def clamp(self, lo: float, hi: float) -> TriangularFuzzyNumber:
        """Restreint le TFN à ``[lo, hi]`` (utile pour borner sur ``[0, 4]``)."""
        ca, cm, cb = (min(max(v, lo), hi) for v in (self.a, self.m, self.b))
        return TriangularFuzzyNumber(ca, cm, cb)

    # ------------------------------------------------------------------ #
    # Arithmétique floue (formes fermées sur grandeurs positives)
    # ------------------------------------------------------------------ #
    def __add__(self, other: TriangularFuzzyNumber) -> TriangularFuzzyNumber:
        return TriangularFuzzyNumber(self.a + other.a, self.m + other.m, self.b + other.b)

    def scale(self, k: float) -> TriangularFuzzyNumber:
        """Multiplication par un scalaire ``k >= 0``."""
        if k < 0:
            raise ValueError("scale exige k >= 0 (grandeurs positives)")
        return TriangularFuzzyNumber(k * self.a, k * self.m, k * self.b)

    def __mul__(self, other: TriangularFuzzyNumber) -> TriangularFuzzyNumber:
        """Produit approché de deux TFN positifs (produit des bornes)."""
        self._require_positive()
        other._require_positive()
        return TriangularFuzzyNumber(self.a * other.a, self.m * other.m, self.b * other.b)

    def __truediv__(self, other: TriangularFuzzyNumber) -> TriangularFuzzyNumber:
        """Quotient approché de deux TFN strictement positifs."""
        self._require_positive()
        other._require_strictly_positive()
        return TriangularFuzzyNumber(self.a / other.b, self.m / other.m, self.b / other.a)

    def _require_positive(self) -> None:
        if self.a < -_TOL:
            raise ValueError(f"opération exige un TFN positif, reçu support [{self.a}, {self.b}]")

    def _require_strictly_positive(self) -> None:
        if self.a <= _TOL:
            raise ValueError(
                f"division exige un dénominateur strictement positif, reçu support "
                f"[{self.a}, {self.b}]"
            )

    def __repr__(self) -> str:  # pragma: no cover - confort de lecture
        return f"TFN({self.a:.4g}, {self.m:.4g}, {self.b:.4g})"


# ---------------------------------------------------------------------- #
# Agrégateurs
# ---------------------------------------------------------------------- #
def fuzzy_sum(items: Iterable[TriangularFuzzyNumber]) -> TriangularFuzzyNumber:
    """Somme floue d'un itérable de TFN."""
    acc = TriangularFuzzyNumber.crisp(0.0)
    for x in items:
        acc = acc + x
    return acc


def fuzzy_weighted_average(
    values: list[TriangularFuzzyNumber],
    weights: list[TriangularFuzzyNumber] | list[float],
) -> TriangularFuzzyNumber:
    """Moyenne pondérée floue ``(Σ w_i · x_i) / (Σ w_i)``.

    C'est l'opérateur d'**agrégation hiérarchique** du moteur : il combine les
    questions en sous-domaines, les sous-domaines en axes, et les axes en score
    global, tout en **propageant l'incertitude** (les largeurs des TFN se
    composent au lieu d'être écrasées comme dans une moyenne classique).

    ``weights`` peut être une liste de scalaires (poids crisp) ou de TFN (poids
    flous issus du Fuzzy AHP).
    """
    if len(values) != len(weights):
        raise ValueError("values et weights doivent avoir la même longueur")
    if not values:
        raise ValueError("agrégation d'une liste vide")

    tfn_weights: list[TriangularFuzzyNumber] = [
        w if isinstance(w, TriangularFuzzyNumber) else TriangularFuzzyNumber.crisp(float(w))
        for w in weights
    ]
    numerator = fuzzy_sum(v * w for v, w in zip(values, tfn_weights, strict=True))
    denominator = fuzzy_sum(tfn_weights)
    if denominator.m <= _TOL:
        raise ValueError("somme des poids nulle")
    return numerator / denominator
