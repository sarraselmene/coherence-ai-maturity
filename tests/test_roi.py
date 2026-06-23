"""Tests du module ROI Monte Carlo (Étape 4)."""

from __future__ import annotations

from maturai.roi.monte_carlo import ROIInputsResolved, simulate_roi

BASE = dict(
    hours_per_week=300.0,
    cost_per_fte=60_000.0,
    ai_budget=200_000.0,
    n_automatable_tasks=12.0,
    measured_gains="Estimés",
    risk_cost="Non",
)


def _inputs(maturity):
    return ROIInputsResolved(maturity_tfn=maturity, **BASE)


def test_distributions_are_sane():
    res = simulate_roi(_inputs((2.5, 3.0, 3.5)), n_simulations=5000)
    assert res.fte_saved.mean > 0
    assert res.annual_savings.mean > 0
    assert 0.0 <= res.prob_roi_positive <= 1.0
    assert res.fte_saved.p10 <= res.fte_saved.median <= res.fte_saved.p90


def test_reproducible_with_seed():
    a = simulate_roi(_inputs((2.0, 2.5, 3.0)), n_simulations=3000, seed=7)
    b = simulate_roi(_inputs((2.0, 2.5, 3.0)), n_simulations=3000, seed=7)
    assert a.annual_savings.mean == b.annual_savings.mean


def test_higher_maturity_yields_more_savings():
    low = simulate_roi(_inputs((1.0, 1.0, 1.0)), n_simulations=5000, seed=1)
    high = simulate_roi(_inputs((3.5, 3.5, 3.5)), n_simulations=5000, seed=1)
    assert high.annual_savings.mean > low.annual_savings.mean


def test_serialization():
    res = simulate_roi(_inputs((2.0, 2.5, 3.0)), n_simulations=1000)
    d = res.to_dict()
    assert "roi_ratio" in d and "fte_saved" in d and "prob_roi_positive" in d
