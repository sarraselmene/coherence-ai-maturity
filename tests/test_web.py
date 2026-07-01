
"""Tests de l'API web (nécessite l'extra ``web`` + httpx — sinon ignorés)."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from maturai.referential import get_default_referential
from maturai.web.app import app

client = TestClient(app)


def _all_answers(score: int = 2) -> dict[str, int]:
    ref = get_default_referential()
    return {q.id: score for q in ref.iter_scored_questions()}


def test_referential_endpoint():
    r = client.get("/api/referential")
    assert r.status_code == 200
    data = r.json()
    assert len(data["axes"]) == 5
    n_questions = sum(len(sd["questions"]) for ax in data["axes"] for sd in ax["subdomains"])
    assert n_questions == 33
    assert data["sectors"]  # liste de secteurs non vide


def test_assess_endpoint_uniform():
    r = client.post("/api/assess", json={"answers": _all_answers(2), "sector": "Santé"})
    assert r.status_code == 200
    data = r.json()
    assert data["score"]["global"]["presented_level"] == pytest.approx(3.0, abs=1e-6)
    assert len(data["score"]["axes"]) == 5
    assert "report_markdown" in data and "# Rapport" in data["report_markdown"]


def test_assess_endpoint_with_roi():
    payload = {
        "answers": _all_answers(3),
        "sector": "Banque/Assurance",
        "roi_inputs": {"hours_per_week": 300, "cost_per_fte": 60000, "ai_budget": 200000,
                       "measured_gains": "Estimés", "risk_cost": "Non"},
    }
    r = client.post("/api/assess", json=payload)
    assert r.status_code == 200
    assert r.json()["roi"] is not None


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "MaturAI" in r.text