"""Génération de profils d'entreprises simulés (Étape 3 / enrichissement point 4).

Le protocole de validation a besoin de profils de référence dont on connaît
*a priori* le comportement attendu :

* **profils cohérents** : tous les axes au même niveau (un débutant homogène, un
  leader homogène…) — le moteur flou doit y produire un score proche de la
  moyenne classique (pas d'incohérence à pénaliser) ;
* **profils incohérents** : axes volontairement contradictoires (stratégie haute
  + gouvernance basse) — le moteur flou doit y produire un score *inférieur* à
  la moyenne classique, et signaler l'incohérence.

C'est exactement le contraste qui démontre l'apport du moteur (vs agrégation
linéaire) dans le mémoire.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from maturai.domain.referential import Referential
from maturai.domain.responses import Assessment, ClientContext, QuestionResponse, ROIInputs


@dataclass(frozen=True)
class ProfileSpec:
    """Spécification d'un profil : niveau cible (0..4) par axe."""

    name: str
    description: str
    axis_targets: dict[str, int]
    is_coherent: bool


def make_assessment(
    spec: ProfileSpec,
    referential: Referential,
    *,
    confidence: float = 1.0,
    jitter: float = 0.0,
    seed: int = 0,
) -> Assessment:
    """Construit un :class:`Assessment` à partir d'une spécification de profil.

    Args:
        jitter: bruit gaussien (écart-type, en niveaux) ajouté à chaque réponse
            pour simuler l'hétérogénéité intra-axe ; les scores restent dans [0,4].
        seed: graine pour la reproductibilité.
    """
    rng = np.random.default_rng(seed)
    responses: list[QuestionResponse] = []
    for ax in referential.axes:
        target = spec.axis_targets.get(ax.id, 2)
        for q in ax.iter_questions():
            noisy = target + (rng.normal(0.0, jitter) if jitter > 0 else 0.0)
            score = int(round(min(max(noisy, 0), 4)))
            responses.append(
                QuestionResponse(question_id=q.id, score=score, confidence=confidence)
            )
    return Assessment(
        client_name=spec.name,
        context=ClientContext(sector="Test", region="France"),
        responses=responses,
        roi_inputs=ROIInputs(),
    )


# --------------------------------------------------------------------------- #
# Catalogue de profils de référence
# --------------------------------------------------------------------------- #
STANDARD_PROFILES: list[ProfileSpec] = [
    ProfileSpec(
        name="Débutant cohérent",
        description="Tous les axes au niveau 1 — démarrage homogène.",
        axis_targets={"strategy": 1, "data": 1, "talents": 1, "technology": 1, "governance": 1},
        is_coherent=True,
    ),
    ProfileSpec(
        name="Intermédiaire cohérent",
        description="Tous les axes au niveau 2.",
        axis_targets={"strategy": 2, "data": 2, "talents": 2, "technology": 2, "governance": 2},
        is_coherent=True,
    ),
    ProfileSpec(
        name="Leader cohérent",
        description="Tous les axes au niveau 4 — maturité homogène élevée.",
        axis_targets={"strategy": 4, "data": 4, "talents": 4, "technology": 4, "governance": 4},
        is_coherent=True,
    ),
    ProfileSpec(
        name="Incohérent : ambition sans gouvernance",
        description="Stratégie/technologie élevées, gouvernance quasi nulle.",
        axis_targets={"strategy": 4, "data": 3, "talents": 3, "technology": 4, "governance": 0},
        is_coherent=False,
    ),
    ProfileSpec(
        name="Incohérent : déploiement sur données faibles",
        description="Technologie élevée mais socle Données très faible.",
        axis_targets={"strategy": 3, "data": 0, "talents": 2, "technology": 4, "governance": 2},
        is_coherent=False,
    ),
    ProfileSpec(
        name="Incohérent : ambition sans talents",
        description="Stratégie élevée mais talents quasi inexistants.",
        axis_targets={"strategy": 4, "data": 2, "talents": 0, "technology": 2, "governance": 2},
        is_coherent=False,
    ),
]


def get_profile(name: str) -> ProfileSpec:
    for p in STANDARD_PROFILES:
        if p.name == name:
            return p
    raise KeyError(f"profil inconnu : {name!r}")
