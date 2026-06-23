"""Entraîne l'ANFIS (distillation) et compare 3 scorings : classique / flou / neuro-flou.

Usage :
    python scripts/run_anfis.py
Nécessite l'extra ``fuzzy`` (torch).
"""

from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

from maturai.anfis.training import train_global_anfis
from maturai.referential import get_default_referential
from maturai.scoring.engine import score_assessment
from maturai.validation.profiles import STANDARD_PROFILES, make_assessment


def main() -> None:
    ref = get_default_referential()

    print("Entraînement de l'ANFIS par distillation du moteur flou...")
    model, metrics = train_global_anfis(ref, n_train=900, n_test=300, epochs=500)
    print(f"Évaluation sur test : MAE={metrics.mae:.3f}  RMSE={metrics.rmse:.3f}  "
          f"corr={metrics.corr:.3f}")
    print("→ L'ANFIS a appris la fonction de scoring (pénalité d'incohérence comprise) "
          "sans qu'on lui donne les règles.\n")

    axis_ids = [ax.id for ax in ref.axes]
    print("Comparaison à trois scorings sur les profils de référence (échelle 0-4) :")
    print(f"{'Profil':<42}{'classique':>10}{'flou':>8}{'ANFIS':>8}")
    for spec in STANDARD_PROFILES:
        assessment = make_assessment(spec, ref, confidence=1.0)
        score = score_assessment(assessment, ref)
        crisp = {a.axis_id: a.crisp for a in score.axes}
        # classique axes -> global : moyenne pondérée linéaire des axes
        w = score.axis_weights
        classic = sum(crisp[a] * w[a] for a in axis_ids) / sum(w[a] for a in axis_ids)
        feats = np.array([[crisp[a] for a in axis_ids]])
        anfis = float(model.predict(feats)[0])
        print(f"{spec.name:<42}{classic:>10.2f}{score.global_crisp:>8.2f}{anfis:>8.2f}")


if __name__ == "__main__":
    main()
