"""Campagne de validation massive (Étape 3 — extension statistique).

Au-delà des quelques profils de référence (:mod:`maturai.validation.profiles`),
on génère un grand nombre de profils **aléatoires** pour obtenir des résultats
*statistiques* (et non anecdotiques) sur l'apport du moteur flou.

Résultat central, non circulaire et démontrable : l'écart `flou − classique`
devient d'autant plus négatif que le profil est **incohérent**, l'incohérence
étant mesurée objectivement par l'**étendue inter-axes**
``spread = max(niveaux) − min(niveaux)``. Autrement dit, plus les axes se
contredisent, plus le moteur flou s'écarte (vers le bas) de l'agrégation
linéaire — exactement ce qu'une moyenne pondérée est incapable de faire.

Ce module ne dépend que de numpy ; le tracé des figures est optionnel
(matplotlib, extra ``dev``).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from maturai.domain.referential import Referential
from maturai.scoring.engine import score_assessment
from maturai.validation.profiles import ProfileSpec, make_assessment


@dataclass(frozen=True)
class CampaignRecord:
    """Une ligne de campagne : un profil aléatoire et ses scores."""

    index: int
    spread: int  # max(niveaux) - min(niveaux) : mesure d'incohérence
    classic: float
    fuzzy: float
    gap: float  # fuzzy - classic
    penalty: float
    n_incoherences: int
    targets: dict[str, int]


def run_campaign(
    referential: Referential,
    n_profiles: int = 500,
    seed: int = 12345,
) -> list[CampaignRecord]:
    """Génère ``n_profiles`` profils aléatoires et calcule leurs scores.

    Chaque axe reçoit un niveau cible tiré uniformément dans ``{0..4}``. Le
    profil est scoré par le moteur flou ; on compare au scoring classique.
    """
    rng = np.random.default_rng(seed)
    axis_ids = [ax.id for ax in referential.axes]
    records: list[CampaignRecord] = []

    for i in range(n_profiles):
        levels = rng.integers(0, 5, size=len(axis_ids))
        targets = {ax_id: int(lvl) for ax_id, lvl in zip(axis_ids, levels, strict=True)}
        spread = int(levels.max() - levels.min())
        spec = ProfileSpec(
            name=f"rand-{i}",
            description="profil aléatoire de campagne",
            axis_targets=targets,
            is_coherent=spread <= 1,
        )
        assessment = make_assessment(spec, referential, confidence=1.0, seed=i)
        score = score_assessment(assessment, referential)
        records.append(
            CampaignRecord(
                index=i,
                spread=spread,
                classic=score.classic_weighted_mean,
                fuzzy=score.global_crisp,
                gap=score.fuzzy_vs_classic_gap,
                penalty=score.incoherence_penalty,
                n_incoherences=len(score.fired_rules),
                targets=targets,
            )
        )
    return records


def gap_by_spread(records: list[CampaignRecord]) -> dict[int, dict[str, float]]:
    """Statistiques de l'écart flou−classique groupées par niveau d'incohérence."""
    out: dict[int, dict[str, float]] = {}
    for s in sorted({r.spread for r in records}):
        gaps = [r.gap for r in records if r.spread == s]
        penalties = [r.penalty for r in records if r.spread == s]
        out[s] = {
            "n": float(len(gaps)),
            "mean_gap": float(np.mean(gaps)),
            "std_gap": float(np.std(gaps)),
            "mean_penalty": float(np.mean(penalties)),
        }
    return out


def correlation_spread_gap(records: list[CampaignRecord]) -> float:
    """Corrélation de Pearson entre étendue inter-axes et écart flou−classique.

    Attendue **négative** : plus l'incohérence est grande, plus le score flou
    s'écarte sous le classique.
    """
    spreads = np.array([r.spread for r in records], dtype=float)
    gaps = np.array([r.gap for r in records], dtype=float)
    if spreads.std() < 1e-12 or gaps.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(spreads, gaps)[0, 1])


def export_csv(records: list[CampaignRecord], path: Path) -> None:
    """Exporte la campagne en CSV (une ligne par profil)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["index", "spread", "classic", "fuzzy", "gap", "penalty", "n_incoherences"])
        for r in records:
            writer.writerow(
                [r.index, r.spread, f"{r.classic:.4f}", f"{r.fuzzy:.4f}",
                 f"{r.gap:.4f}", f"{r.penalty:.4f}", r.n_incoherences]
            )


def plot_gap_vs_spread(records: list[CampaignRecord], path: Path) -> bool:
    """Trace l'écart flou−classique en fonction de l'incohérence (matplotlib).

    Renvoie ``False`` si matplotlib n'est pas installé.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:  # pragma: no cover - dépendance optionnelle
        return False

    stats = gap_by_spread(records)
    spreads = sorted(stats.keys())
    means = [stats[s]["mean_gap"] for s in spreads]
    stds = [stats[s]["std_gap"] for s in spreads]

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    jitter = np.random.default_rng(0).normal(0, 0.05, size=len(records))
    ax.scatter(
        [r.spread + j for r, j in zip(records, jitter, strict=True)],
        [r.gap for r in records],
        alpha=0.25, s=12, label="profils", color="#1f77b4",
    )
    ax.errorbar(spreads, means, yerr=stds, color="#d62728", marker="o",
                capsize=4, label="écart moyen ± σ", linewidth=2)
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Incohérence inter-axes  (max − min des niveaux)")
    ax.set_ylabel("Écart  score flou − score classique")
    ax.set_title("Le moteur flou pénalise spécifiquement les profils incohérents")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return True


def summarize_campaign(records: list[CampaignRecord]) -> dict:
    """Synthèse exploitable pour le mémoire."""
    coherent = [r.gap for r in records if r.spread <= 1]
    incoherent = [r.gap for r in records if r.spread >= 3]
    return {
        "n_profiles": len(records),
        "correlation_spread_gap": correlation_spread_gap(records),
        "mean_gap_coherent_spread_le_1": float(np.mean(coherent)) if coherent else 0.0,
        "mean_gap_incoherent_spread_ge_3": float(np.mean(incoherent)) if incoherent else 0.0,
        "by_spread": gap_by_spread(records),
    }
