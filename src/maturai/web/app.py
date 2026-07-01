"""Application web FastAPI — interface d'évaluation de la maturité IA (étape 7).

Expose :
* ``GET /``                  → la SPA (questionnaire + résultats) ;
* ``GET /api/referential``   → le questionnaire structuré (contexte, axes, ROI) ;
* ``POST /api/assess``       → calcule le score flou + ROI + rapport.

Le backend réutilise tel quel le cœur scientifique (``maturai.scoring``,
``maturai.roi``, ``maturai.reporting``) : l'interface n'est qu'une couche de
présentation, conformément à l'architecture en couches.

Lancement :
    pip install -e ".[web]"
    python scripts/run_web.py        # http://127.0.0.1:8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from maturai.domain.referential import Referential
from maturai.domain.responses import (
    Assessment,
    ClientContext,
    QuestionResponse,
    ROIInputs,
)
from maturai.referential import get_default_referential
from maturai.reporting import render_markdown_report
from maturai.roi import build_roi_inputs, simulate_roi
from maturai.scoring.engine import score_assessment
from maturai.web.schemas import AssessRequest, AssessResponse

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="MaturAI — Évaluation de la maturité IA", version="0.1.0")


# --------------------------------------------------------------------------- #
# Sérialisation du référentiel pour le front
# --------------------------------------------------------------------------- #
def _referential_payload(ref: Referential) -> dict:
    sectors: list[str] = []
    context_questions = []
    for q in ref.context_section.questions:
        context_questions.append(
            {"id": q.id, "field": q.field, "text": q.text, "type": q.type, "options": q.options}
        )
        if q.field == "sector":
            sectors = q.options

    axes = []
    for ax in ref.axes:
        subdomains = []
        for sd in ax.subdomains:
            questions = []
            for q in sd.questions:
                questions.append(
                    {
                        "id": q.id,
                        "text": q.text,
                        "layer": q.layer,
                        "sources": q.referential.sources,
                        "justification": q.referential.justification,
                        "levels": [{"score": lvl.score, "label": lvl.label} for lvl in q.levels],
                    }
                )
            subdomains.append({"id": sd.id, "name": sd.name, "questions": questions})
        axes.append(
            {
                "id": ax.id,
                "name": ax.name,
                "code": ax.code,
                "anchor": ax.anchor,
                "subdomains": subdomains,
            }
        )

    roi_inputs = [
        {
            "id": ri.id,
            "field": ri.field,
            "text": ri.text,
            "type": ri.type,
            "unit": ri.unit,
            "options": ri.options,
        }
        for ri in ref.roi_module.inputs
    ]

    return {
        "meta": {
            "name": ref.meta.name,
            "version": ref.meta.version,
            "level_labels": ref.meta.level_labels,
            "scale": ref.meta.scale.model_dump(),
            "sources": {k: v.label for k, v in ref.meta.referential_sources.items()},
        },
        "sectors": sectors,
        "context_questions": context_questions,
        "axes": axes,
        "roi_inputs": roi_inputs,
    }


# --------------------------------------------------------------------------- #
# Routes API
# --------------------------------------------------------------------------- #
@app.get("/api/referential")
def get_referential() -> dict:
    return _referential_payload(get_default_referential())


@app.post("/api/assess", response_model=AssessResponse)
def assess(req: AssessRequest) -> AssessResponse:
    ref = get_default_referential()

    responses = [
        QuestionResponse(
            question_id=qid,
            score=int(score),
            confidence=float(req.confidences.get(qid, 1.0)),
        )
        for qid, score in req.answers.items()
    ]
    context = ClientContext(sector=req.sector, **{k: v for k, v in req.context.items()})
    roi_inputs = _build_roi_inputs(req.roi_inputs)
    assessment = Assessment(
        client_name=req.client_name or "Client",
        context=context,
        responses=responses,
        roi_inputs=roi_inputs,
    )

    score = score_assessment(assessment, ref)

    roi_dict = None
    if roi_inputs.ai_budget > 0 and roi_inputs.hours_per_week > 0:
        roi = simulate_roi(
            build_roi_inputs(
                roi_inputs, (score.global_tfn.a, score.global_tfn.m, score.global_tfn.b)
            )
        )
        roi_dict = roi.to_dict()

    report = render_markdown_report(
        score,
        sector=req.sector,
        roi=None if roi_dict is None else _RoiView(roi_dict),
    )
    return AssessResponse(score=score.to_dict(), roi=roi_dict, report_markdown=report)


def _build_roi_inputs(raw: dict) -> ROIInputs:
    def num(key: str) -> float:
        try:
            return float(raw.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    return ROIInputs(
        n_automatable_tasks=num("n_automatable_tasks"),
        hours_per_week=num("hours_per_week"),
        cost_per_fte=num("cost_per_fte"),
        ai_budget=num("ai_budget"),
        measured_gains=_as_str(raw.get("measured_gains")),
        risk_cost=_as_str(raw.get("risk_cost")),
    )


def _as_str(v: object) -> str | None:
    return str(v) if v not in (None, "") else None


class _RoiView:
    """Adapte un dict ROI à l'interface attendue par ``render_markdown_report``."""

    class _Dist:
        def __init__(self, d: dict) -> None:
            self.median = d["median"]
            self.p10 = d["p10"]
            self.p90 = d["p90"]

    def __init__(self, d: dict) -> None:
        self.fte_saved = self._Dist(d["fte_saved"])
        self.annual_savings = self._Dist(d["annual_savings_eur"])
        self.roi_ratio = self._Dist(d["roi_ratio"])
        self.prob_roi_positive = d["prob_roi_positive"]


# --------------------------------------------------------------------------- #
# SPA statique (montée en dernier pour ne pas masquer les routes /api)
# --------------------------------------------------------------------------- #
@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
