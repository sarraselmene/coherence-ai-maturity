"""Génère un rapport de maturité IA (hors-ligne, déterministe) pour un profil.

Usage :
    python scripts/run_report.py            # profil incohérent par défaut
    python scripts/run_report.py "Leader cohérent"
Écrit le rapport Markdown dans outputs/rapport.md.
"""

from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from maturai.config import PROJECT_ROOT
from maturai.domain.responses import ROIInputs
from maturai.referential import get_default_referential
from maturai.reporting import render_markdown_report
from maturai.roi import build_roi_inputs, simulate_roi
from maturai.scoring.engine import score_assessment
from maturai.validation.profiles import STANDARD_PROFILES, get_profile, make_assessment


def main() -> None:
    ref = get_default_referential()
    name = sys.argv[1] if len(sys.argv) > 1 else "Incohérent : ambition sans gouvernance"
    try:
        spec = get_profile(name)
    except KeyError:
        print(f"Profil inconnu. Disponibles : {[p.name for p in STANDARD_PROFILES]}")
        sys.exit(1)

    assessment = make_assessment(spec, ref, confidence=1.0)
    score = score_assessment(assessment, ref)

    roi_inputs = ROIInputs(hours_per_week=350, cost_per_fte=62000, ai_budget=250000,
                           measured_gains="Estimés", risk_cost="Estimation grossière")
    roi = simulate_roi(
        build_roi_inputs(roi_inputs, (score.global_tfn.a, score.global_tfn.m, score.global_tfn.b))
    )

    report = render_markdown_report(score, sector="Banque/Assurance", roi=roi)
    out = PROJECT_ROOT / "outputs" / "rapport.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[Rapport écrit dans {out}]")


if __name__ == "__main__":
    main()
