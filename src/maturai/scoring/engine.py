"""Moteur de scoring — orchestration de bout en bout (Étape 2).

Pipeline complet :

1. **Pondération** : poids d'axes par Fuzzy AHP (repli sur les poids du
   référentiel si la matrice est indisponible).
2. **Fuzzification** : chaque réponse → TFN (incertitude dès l'entrée).
3. **Agrégation hiérarchique floue** : questions → sous-domaines → axes → global
   (l'incertitude se propage, point 3).
4. **Défuzzification** des TFN d'axes → scores crisp.
5. **Inférence Mamdani** : pénalité d'incohérence inter-axes.
6. **Score final** = global brut − pénalité, borné sur ``[0, 4]``.
7. **Baseline** : moyenne pondérée linéaire classique calculée en parallèle,
   pour quantifier l'apport du moteur flou (argument du mémoire).

Le moteur est **pur** (aucun effet de bord, aucune dépendance réseau) : il prend
un :class:`Assessment` et un :class:`Referential`, et renvoie un
:class:`AssessmentScore`. C'est ce qui le rend testable isolément (exigence de
l'étape 2 : « tester le moteur sans interface ni LLM autour »).
"""

from __future__ import annotations

from maturai.config import DEFAULT_SCORING, ScoringConfig
from maturai.domain.fuzzy_number import TriangularFuzzyNumber as TFN
from maturai.domain.referential import Axis, Referential, SubDomain
from maturai.domain.responses import Assessment, QuestionResponse
from maturai.scoring.aggregation import aggregate
from maturai.scoring.fuzzification import fuzzify_response
from maturai.scoring.inference import infer_incoherence_penalty
from maturai.scoring.results import (
    AssessmentScore,
    AxisScore,
    QuestionScore,
    SubDomainScore,
)


def _resolve_axis_weights(ref: Referential) -> dict[str, float]:
    """Poids d'axes : Fuzzy AHP si possible, sinon repli du référentiel.

    Les poids sont restreints aux axes présents et renormalisés à somme 1.
    """
    present = [ax.id for ax in ref.axes]
    weights: dict[str, float]
    try:
        from maturai.weighting.fuzzy_ahp import load_axis_weights

        result = load_axis_weights()
        weights = {ax_id: result.weights.get(ax_id, 0.0) for ax_id in present}
        if sum(weights.values()) <= 0:  # pragma: no cover - cas dégénéré
            raise ValueError("poids AHP nuls")
    except Exception:
        weights = {ax.id: ax.weight for ax in ref.axes}

    total = sum(weights.values())
    if total <= 0:  # pragma: no cover - cas dégénéré
        return {ax_id: 1.0 / len(present) for ax_id in present}
    return {k: v / total for k, v in weights.items()}


def _score_subdomain(
    sd: SubDomain,
    responses: dict[str, QuestionResponse],
    config: ScoringConfig,
) -> SubDomainScore | None:
    """Score d'un sous-domaine, ou ``None`` si aucune question n'a de réponse."""
    q_scores: list[QuestionScore] = []
    tfns: list[TFN] = []
    weights: list[float] = []
    for q in sd.questions:
        resp = responses.get(q.id)
        if resp is None:
            continue  # question non répondue : exclue de l'agrégation
        tfn = fuzzify_response(resp, config)
        q_scores.append(
            QuestionScore(question_id=q.id, layer=q.layer, tfn=tfn, crisp=tfn.defuzzify())
        )
        tfns.append(tfn)
        weights.append(q.weight)

    if not tfns:
        return None
    sd_tfn = aggregate(tfns, weights)
    return SubDomainScore(
        subdomain_id=sd.id,
        name=sd.name,
        tfn=sd_tfn,
        crisp=sd_tfn.defuzzify(),
        questions=q_scores,
    )


def _score_axis(
    axis: Axis,
    responses: dict[str, QuestionResponse],
    weight: float,
    config: ScoringConfig,
) -> AxisScore | None:
    sd_scores: list[SubDomainScore] = []
    tfns: list[TFN] = []
    weights: list[float] = []
    for sd in axis.subdomains:
        sd_score = _score_subdomain(sd, responses, config)
        if sd_score is None:
            continue
        sd_scores.append(sd_score)
        tfns.append(sd_score.tfn)
        weights.append(sd.weight)

    if not tfns:
        return None
    axis_tfn = aggregate(tfns, weights)
    return AxisScore(
        axis_id=axis.id,
        name=axis.name,
        tfn=axis_tfn,
        crisp=axis_tfn.defuzzify(),
        weight=weight,
        subdomains=sd_scores,
    )


def _classic_weighted_mean(
    ref: Referential,
    responses: dict[str, QuestionResponse],
    axis_weights: dict[str, float],
) -> float:
    """Baseline : agrégation linéaire crisp (moyenne pondérée hiérarchique).

    Utilise les scores bruts (non fuzzifiés) et les mêmes poids, afin d'isoler
    l'effet propre du traitement flou + inférence d'incohérence.
    """

    def mean(values: list[float], weights: list[float]) -> float | None:
        if not values:
            return None
        tot = sum(weights)
        return sum(v * w for v, w in zip(values, weights, strict=True)) / tot if tot else None

    axis_means: list[float] = []
    axis_ws: list[float] = []
    for ax in ref.axes:
        sd_means: list[float] = []
        sd_ws: list[float] = []
        for sd in ax.subdomains:
            q_vals = [responses[q.id].score for q in sd.questions if q.id in responses]
            q_ws = [q.weight for q in sd.questions if q.id in responses]
            m = mean([float(v) for v in q_vals], q_ws)
            if m is not None:
                sd_means.append(m)
                sd_ws.append(sd.weight)
        axm = mean(sd_means, sd_ws)
        if axm is not None:
            axis_means.append(axm)
            axis_ws.append(axis_weights.get(ax.id, ax.weight))
    result = mean(axis_means, axis_ws)
    return result if result is not None else 0.0


def score_assessment(
    assessment: Assessment,
    referential: Referential | None = None,
    config: ScoringConfig = DEFAULT_SCORING,
    *,
    credibility_alpha: float = 0.5,
) -> AssessmentScore:
    """Calcule le score complet d'une évaluation.

    Args:
        assessment: réponses + contexte + variables ROI.
        referential: référentiel (chargé par défaut si ``None``).
        config: hyperparamètres du moteur.
        credibility_alpha: niveau de la coupe-alpha pour l'intervalle de
            crédibilité du score global (0.5 par défaut).
    """
    if referential is None:
        from maturai.referential.loader import get_default_referential

        referential = get_default_referential()

    responses = assessment.responses_by_id()
    axis_weights = _resolve_axis_weights(referential)

    # Scores par axe
    axis_scores: list[AxisScore] = []
    axis_tfns: list[TFN] = []
    axis_ws: list[float] = []
    for ax in referential.axes:
        ax_score = _score_axis(ax, responses, axis_weights.get(ax.id, ax.weight), config)
        if ax_score is None:
            continue
        axis_scores.append(ax_score)
        axis_tfns.append(ax_score.tfn)
        axis_ws.append(axis_weights.get(ax.id, ax.weight))

    if not axis_tfns:
        raise ValueError("aucune réponse exploitable : impossible de calculer un score")

    # Agrégation globale floue
    global_tfn = aggregate(axis_tfns, axis_ws)
    global_raw_crisp = global_tfn.defuzzify()

    # Inférence d'incohérence inter-axes (Mamdani)
    axis_crisp = {a.axis_id: a.crisp for a in axis_scores}
    inference = infer_incoherence_penalty(axis_crisp, config=config)

    global_crisp = min(
        max(global_raw_crisp - inference.penalty, config.scale_min), config.scale_max
    )

    # Intervalle de crédibilité : coupe-alpha du TFN global (largeur = incertitude
    # des données), décalé de la pénalité déterministe pour rester centré sur le
    # score FINAL, puis borné sur [scale_min, scale_max].
    lo, hi = global_tfn.alpha_cut(credibility_alpha)
    lo -= inference.penalty
    hi -= inference.penalty
    credibility = (
        max(lo, config.scale_min),
        min(hi, config.scale_max),
    )

    classic = _classic_weighted_mean(referential, responses, axis_weights)

    return AssessmentScore(
        client_name=assessment.client_name,
        axes=axis_scores,
        global_tfn=global_tfn,
        global_raw_crisp=global_raw_crisp,
        incoherence_penalty=inference.penalty,
        global_crisp=global_crisp,
        fired_rules=inference.fired_rules,
        classic_weighted_mean=classic,
        credibility_interval=credibility,
        axis_weights=axis_weights,
    )
