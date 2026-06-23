"""Validation sémantique du référentiel.

Au-delà de la validation structurelle (jsonschema), on vérifie ici les
invariants *métier* dont dépendent les briques aval :

* unicité des identifiants de questions ;
* poids strictement positifs (un poids nul ferait disparaître une question de
  l'agrégation sans avertissement) ;
* sources de traçabilité connues (déclarées dans ``meta.referential_sources``) ;
* couverture : chaque axe a au moins une question.

Toute violation lève :class:`ReferentialError` — on échoue tôt et clairement
plutôt que de produire un score sur un référentiel corrompu.
"""

from __future__ import annotations

from maturai.domain.referential import Referential


class ReferentialError(ValueError):
    """Référentiel sémantiquement invalide."""


def validate_referential(ref: Referential) -> None:
    """Lève :class:`ReferentialError` si un invariant métier est violé."""
    errors: list[str] = []

    # 1. Unicité des identifiants de questions notées
    ids = ref.question_ids()
    duplicates = {qid for qid in ids if ids.count(qid) > 1}
    if duplicates:
        errors.append(f"identifiants de questions dupliqués : {sorted(duplicates)}")

    # 2. Poids strictement positifs
    for ax in ref.axes:
        if ax.weight <= 0:
            errors.append(f"axe {ax.id!r} : poids <= 0 ({ax.weight})")
        for sd in ax.subdomains:
            if sd.weight <= 0:
                errors.append(f"sous-domaine {sd.id!r} : poids <= 0 ({sd.weight})")
            if not sd.questions:
                errors.append(f"sous-domaine {sd.id!r} : aucune question")
            for q in sd.questions:
                if q.weight <= 0:
                    errors.append(f"question {q.id!r} : poids <= 0 ({q.weight})")

    # 3. Sources de traçabilité connues
    known_sources = set(ref.meta.referential_sources.keys())
    for q in ref.iter_scored_questions():
        unknown = set(q.referential.sources) - known_sources
        if unknown:
            errors.append(f"question {q.id!r} : sources inconnues {sorted(unknown)}")

    # 4. Couverture des axes
    for ax in ref.axes:
        if not ax.iter_questions():
            errors.append(f"axe {ax.id!r} : aucune question notée")

    # 5. Poids de repli cohérents avec les axes présents
    fallback = ref.meta.weighting.fallback_axis_weights
    missing = {ax.id for ax in ref.axes} - set(fallback.keys())
    if missing:
        errors.append(f"poids de repli manquants pour les axes : {sorted(missing)}")

    if errors:
        raise ReferentialError(
            "Référentiel invalide :\n  - " + "\n  - ".join(errors)
        )


def coverage_report(ref: Referential) -> dict[str, dict[str, int]]:
    """Compte des questions par axe et par couche (generic/ai_specific).

    Utile pour le mémoire : matérialise le double ancrage (combien de questions
    génériques vs IA-spécifiques par axe).
    """
    report: dict[str, dict[str, int]] = {}
    for ax in ref.axes:
        qs = ax.iter_questions()
        report[ax.id] = {
            "total": len(qs),
            "generic": sum(1 for q in qs if q.layer == "generic"),
            "ai_specific": sum(1 for q in qs if q.layer == "ai_specific"),
        }
    return report
