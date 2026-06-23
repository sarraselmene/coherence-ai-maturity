"""Tests du protocole de validation (Étape 3) : flou vs classique."""

from __future__ import annotations

from maturai.validation import STANDARD_PROFILES, compare_profiles, summarize


def test_compare_returns_one_row_per_profile(referential):
    rows = compare_profiles(STANDARD_PROFILES, referential)
    assert len(rows) == len(STANDARD_PROFILES)


def test_incoherent_profiles_more_penalized_than_coherent(referential):
    rows = compare_profiles(STANDARD_PROFILES, referential)
    stats = summarize(rows)
    # l'écart flou-classique est plus négatif sur les profils incohérents
    assert stats["mean_gap_incoherent"] < stats["mean_gap_coherent"]
    assert stats["mean_penalty_incoherent"] > 0.0


def test_coherent_profiles_have_no_incoherence(referential):
    rows = compare_profiles(STANDARD_PROFILES, referential)
    for r in rows:
        if r.is_coherent:
            assert r.n_incoherences == 0


def test_every_incoherent_profile_flags_at_least_one_rule(referential):
    rows = compare_profiles(STANDARD_PROFILES, referential)
    for r in rows:
        if not r.is_coherent:
            assert r.n_incoherences >= 1
