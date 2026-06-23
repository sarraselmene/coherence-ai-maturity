"""MaturAI — Outil d'évaluation de la maturité IA.

Package racine. Expose les points d'entrée de haut niveau :

>>> from maturai import load_referential, score_assessment
"""

from maturai.referential.loader import load_referential
from maturai.scoring.engine import score_assessment

__version__ = "0.1.0"

__all__ = ["load_referential", "score_assessment", "__version__"]
