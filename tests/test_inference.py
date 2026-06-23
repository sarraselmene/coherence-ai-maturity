"""Tests de l'inférence Mamdani d'incohérence inter-axes."""

from __future__ import annotations

from maturai.config import ScoringConfig
from maturai.scoring.inference import infer_incoherence_penalty
from maturai.scoring.rules import axis_term_degree

COHERENT = {"strategy": 2.0, "data": 2.0, "talents": 2.0, "technology": 2.0, "governance": 2.0}
LEADER = {"strategy": 4.0, "data": 4.0, "talents": 4.0, "technology": 4.0, "governance": 4.0}
AMBITION_NO_GOV = {
    "strategy": 4.0,
    "data": 3.0,
    "talents": 3.0,
    "technology": 4.0,
    "governance": 0.0,
}


def test_axis_terms():
    assert axis_term_degree(0.0, "LOW") == 1.0
    assert axis_term_degree(4.0, "HIGH") == 1.0
    assert axis_term_degree(2.0, "MED") == 1.0


def test_coherent_profile_no_penalty():
    res = infer_incoherence_penalty(COHERENT)
    assert res.penalty == 0.0
    assert not res.has_incoherence


def test_coherent_leader_no_penalty():
    res = infer_incoherence_penalty(LEADER)
    assert res.penalty == 0.0
    assert not res.fired_rules


def test_incoherent_profile_penalized():
    res = infer_incoherence_penalty(AMBITION_NO_GOV)
    assert res.penalty > 0.0
    assert res.has_incoherence
    names = {r.name for r in res.fired_rules}
    assert "ambition_sans_gouvernance" in names


def test_disabling_incoherence():
    cfg = ScoringConfig(incoherence_enabled=False)
    res = infer_incoherence_penalty(AMBITION_NO_GOV, config=cfg)
    assert res.penalty == 0.0
