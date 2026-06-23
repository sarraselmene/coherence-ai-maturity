"""Tests de la campagne de validation massive."""

from __future__ import annotations

from maturai.validation.campaign import (
    correlation_spread_gap,
    run_campaign,
    summarize_campaign,
)


def test_campaign_size(referential):
    records = run_campaign(referential, n_profiles=120, seed=1)
    assert len(records) == 120


def test_correlation_is_negative(referential):
    # Plus l'incohérence (spread) est grande, plus l'écart flou-classique est négatif.
    records = run_campaign(referential, n_profiles=300, seed=2)
    assert correlation_spread_gap(records) < 0


def test_incoherent_more_penalized_than_coherent(referential):
    records = run_campaign(referential, n_profiles=300, seed=3)
    s = summarize_campaign(records)
    assert s["mean_gap_incoherent_spread_ge_3"] < s["mean_gap_coherent_spread_le_1"]
