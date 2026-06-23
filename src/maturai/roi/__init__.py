"""Module ROI / ETP (Monte Carlo) — Étape 4 / enrichissement point 6."""

from maturai.roi.monte_carlo import (
    Distribution,
    ROIInputsResolved,
    ROIResult,
    build_roi_inputs,
    simulate_roi,
)

__all__ = [
    "simulate_roi",
    "build_roi_inputs",
    "ROIResult",
    "ROIInputsResolved",
    "Distribution",
]
