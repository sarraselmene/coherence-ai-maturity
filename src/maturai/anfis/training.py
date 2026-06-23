"""Entraînement de l'ANFIS par distillation du moteur flou (Étape 2b).

En l'absence d'historique client étiqueté, on **distille** le moteur Mamdani :
l'ANFIS apprend la fonction *scores d'axes → score global* (incohérences
comprises) à partir de milliers de profils simulés notés par le moteur. Il
apprend donc la pénalité d'incohérence **sans qu'on lui fournisse les règles** —
preuve que la fonction de scoring est apprenable depuis des exemples.

C'est un *bootstrap* : une fois des labels experts disponibles, le même ANFIS se
ré-entraîne/affine sur ces données réelles (cf. ``docs/methodology/03-anfis.md``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from maturai.anfis.model import ANFIS, ANFISConfig
from maturai.domain.referential import Referential
from maturai.scoring.engine import score_assessment
from maturai.validation.profiles import ProfileSpec, make_assessment


def build_distillation_dataset(
    referential: Referential,
    n_samples: int = 1000,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Construit (X = scores d'axes, y = score global) via le moteur flou.

    Returns:
        X: matrice (n_samples, n_axes) des scores crisp d'axes.
        y: vecteur (n_samples,) des scores globaux du moteur.
        axis_ids: ordre des colonnes de X.
    """
    rng = np.random.default_rng(seed)
    axis_ids = [ax.id for ax in referential.axes]
    X, y = [], []
    for i in range(n_samples):
        levels = rng.integers(0, 5, size=len(axis_ids))
        targets = {ax_id: int(lvl) for ax_id, lvl in zip(axis_ids, levels, strict=True)}
        spec = ProfileSpec(name=f"d{i}", description="", axis_targets=targets, is_coherent=True)
        assessment = make_assessment(spec, referential, confidence=1.0, seed=i)
        score = score_assessment(assessment, referential)
        crisp_by_axis = {a.axis_id: a.crisp for a in score.axes}
        X.append([crisp_by_axis[a] for a in axis_ids])
        y.append(score.global_crisp)
    return np.array(X), np.array(y), axis_ids


@dataclass(frozen=True)
class ANFISMetrics:
    mae: float
    rmse: float
    corr: float
    n_train: int
    n_test: int

    def to_dict(self) -> dict:
        return {
            "mae": round(self.mae, 4),
            "rmse": round(self.rmse, 4),
            "corr": round(self.corr, 4),
            "n_train": self.n_train,
            "n_test": self.n_test,
        }


def train_global_anfis(
    referential: Referential,
    n_train: int = 900,
    n_test: int = 300,
    epochs: int = 500,
    seed: int = 0,
) -> tuple[ANFIS, ANFISMetrics]:
    """Entraîne un ANFIS à reproduire le scoring global, évalué sur un test set."""
    X_tr, y_tr, axis_ids = build_distillation_dataset(referential, n_train, seed=seed)
    X_te, y_te, _ = build_distillation_dataset(referential, n_test, seed=seed + 10_000)

    config = ANFISConfig(n_inputs=len(axis_ids), epochs=epochs, seed=seed)
    model = ANFIS(config).fit(X_tr, y_tr)

    pred = model.predict(X_te)
    err = pred - y_te
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    corr = float(np.corrcoef(pred, y_te)[0, 1]) if y_te.std() > 1e-9 else 0.0
    return model, ANFISMetrics(mae=mae, rmse=rmse, corr=corr, n_train=n_train, n_test=n_test)
