"""Tests de l'ANFIS (nécessite torch — sinon les tests sont ignorés)."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("torch")

from maturai.anfis.model import ANFIS, ANFISConfig
from maturai.anfis.training import train_global_anfis


def test_anfis_fits_simple_function():
    # ANFIS doit apprendre une fonction lisse simple : y = moyenne des entrées.
    rng = np.random.default_rng(0)
    X = rng.uniform(0, 4, size=(400, 3))
    y = X.mean(axis=1)
    model = ANFIS(ANFISConfig(n_inputs=3, epochs=300, seed=0)).fit(X, y)
    pred = model.predict(X)
    assert np.mean(np.abs(pred - y)) < 0.3
    # la perte diminue bien au cours de l'entraînement
    assert model.history_[-1] < model.history_[0]


def test_predict_bounds():
    rng = np.random.default_rng(1)
    X = rng.uniform(0, 4, size=(50, 2))
    model = ANFIS(ANFISConfig(n_inputs=2, epochs=50)).fit(X, X.mean(axis=1))
    pred = model.predict(X)
    assert pred.min() >= 0.0 and pred.max() <= 4.0


def test_distillation_recovers_engine(referential):
    # L'ANFIS apprend le scoring global du moteur (incohérences comprises).
    _, metrics = train_global_anfis(referential, n_train=250, n_test=100, epochs=200)
    assert metrics.corr > 0.8
    assert metrics.mae < 0.6
