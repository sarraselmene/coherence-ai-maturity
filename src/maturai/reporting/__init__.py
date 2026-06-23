"""Génération du rapport LLM (Étape 6 / couche 4)."""

from maturai.reporting.generator import (
    ReportGenerator,
    build_report_prompt,
)
from maturai.reporting.kpis import KPI_CATALOG, kpis_for_axis
from maturai.reporting.offline import render_markdown_report

__all__ = [
    "ReportGenerator",
    "build_report_prompt",
    "render_markdown_report",
    "KPI_CATALOG",
    "kpis_for_axis",
]
