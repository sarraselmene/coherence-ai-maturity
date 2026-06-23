"""Protocole de validation (Étape 3 / enrichissement point 4)."""

from maturai.validation.campaign import (
    CampaignRecord,
    correlation_spread_gap,
    export_csv,
    gap_by_spread,
    plot_gap_vs_spread,
    run_campaign,
    summarize_campaign,
)
from maturai.validation.compare import (
    ComparisonRow,
    compare_profiles,
    summarize,
)
from maturai.validation.profiles import (
    STANDARD_PROFILES,
    ProfileSpec,
    get_profile,
    make_assessment,
)

__all__ = [
    "STANDARD_PROFILES",
    "ProfileSpec",
    "make_assessment",
    "get_profile",
    "compare_profiles",
    "summarize",
    "ComparisonRow",
    "run_campaign",
    "CampaignRecord",
    "gap_by_spread",
    "correlation_spread_gap",
    "summarize_campaign",
    "export_csv",
    "plot_gap_vs_spread",
]
