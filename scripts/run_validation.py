"""Campagne de validation : scoring flou vs classique sur N profils aléatoires.

Produit (dans ``outputs/``) :
* ``validation_campaign.csv`` — une ligne par profil ;
* ``validation_gap_vs_spread.png`` — figure de l'écart vs incohérence ;
et imprime la synthèse statistique (corrélation, écarts moyens).

Usage :
    python scripts/run_validation.py [n_profiles]
"""

from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from maturai.config import PROJECT_ROOT
from maturai.referential import get_default_referential
from maturai.validation import (
    export_csv,
    gap_by_spread,
    plot_gap_vs_spread,
    run_campaign,
    summarize_campaign,
)


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    ref = get_default_referential()
    print(f"Campagne de {n} profils aléatoires...")
    records = run_campaign(ref, n_profiles=n)

    summary = summarize_campaign(records)
    print(f"\nCorrélation (incohérence, écart flou−classique) = "
          f"{summary['correlation_spread_gap']:.3f}  (attendue < 0)")
    print(f"Écart moyen  cohérents (spread≤1)   = "
          f"{summary['mean_gap_coherent_spread_le_1']:.3f}")
    print(f"Écart moyen  incohérents (spread≥3) = "
          f"{summary['mean_gap_incoherent_spread_ge_3']:.3f}")

    print("\nÉcart moyen par niveau d'incohérence :")
    print(f"{'spread':>7}{'n':>6}{'écart moyen':>14}{'pénalité moy.':>15}")
    for spread, st in gap_by_spread(records).items():
        print(f"{spread:>7}{int(st['n']):>6}{st['mean_gap']:>14.3f}{st['mean_penalty']:>15.3f}")

    out = PROJECT_ROOT / "outputs"
    csv_path = out / "validation_campaign.csv"
    png_path = out / "validation_gap_vs_spread.png"
    export_csv(records, csv_path)
    print(f"\nCSV exporté : {csv_path}")
    if plot_gap_vs_spread(records, png_path):
        print(f"Figure exportée : {png_path}")
    else:
        print("matplotlib indisponible — figure non générée (pip install -e \".[dev]\").")


if __name__ == "__main__":
    main()
