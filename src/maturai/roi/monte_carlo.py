"""Module ROI / ETP par simulation de Monte Carlo (Étape 4 / enrichissement point 6).

Principe
--------
Plutôt que de produire un ROI ponctuel (faussement précis), on simule des
milliers de scénarios en échantillonnant les paramètres incertains, et on
restitue une **distribution** : ROI médian, intervalle P10–P90, et probabilité
que le ROI soit positif. Cette approche consomme directement le **score de
maturité et son incertitude** (le TFN global), conformément au point 6 de
l'enrichissement.

Modèle (volontairement simple et justifié)
------------------------------------------
1. Heures annuelles sur les tâches automatisables :
   ``H = hours_per_week × WEEKS_PER_YEAR``
2. Fraction réellement automatisable/réalisable ``r`` : variable aléatoire dont
   le **mode dépend de la maturité** (une organisation peu mature ne capte
   qu'une faible part du potentiel théorique) et dont la **dispersion dépend de
   la fiabilité** déclarée des gains (Q41).
3. ETP économisés : ``FTE = H × r / HOURS_PER_FTE_YEAR``
4. Gains bruts annuels : ``G = FTE × cost_per_fte``
5. Coût du risque IA ``risk`` (Q43) : provision échantillonnée, soustraite.
6. Bénéfice net : ``N = G − ai_budget − risk`` ; ``ROI = N / ai_budget``.

Toutes les hypothèses chiffrées sont des constantes documentées ci-dessous, donc
auditables et modifiables — à l'opposé des « boîtes noires » des grilles
commerciales.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --- Constantes du modèle (documentées, ajustables) ----------------------- #
WEEKS_PER_YEAR = 47.0  # semaines travaillées (congés/jours fériés déduits)
HOURS_PER_FTE_YEAR = 1_600.0  # heures productives annuelles par ETP (conservateur)

# Dispersion de la fraction réalisable selon la fiabilité des gains (Q41).
# Plus les gains sont mesurés, plus l'estimation est resserrée.
_RELIABILITY_SPREAD = {
    "Oui avec métriques": 0.10,
    "Estimés": 0.20,
    "Non mesurés": 0.30,
}
_DEFAULT_SPREAD = 0.25

# Provision de risque IA (Q43), en fraction du budget IA, selon le niveau de
# chiffrage déclaré. « Non » => risque latent supposé plus élevé et plus incertain.
_RISK_PROVISION = {
    "Oui chiffré": (0.05, 0.10, 0.15),
    "Estimation grossière": (0.05, 0.15, 0.30),
    "Non": (0.10, 0.25, 0.45),
}
_DEFAULT_RISK = (0.10, 0.25, 0.45)


@dataclass(frozen=True)
class ROIInputsResolved:
    """Variables ROI factuelles + maturité, prêtes pour la simulation."""

    hours_per_week: float
    cost_per_fte: float
    ai_budget: float
    n_automatable_tasks: float
    measured_gains: str | None
    risk_cost: str | None
    maturity_tfn: tuple[float, float, float]  # (a, m, b) du score global sur [0,4]


@dataclass(frozen=True)
class Distribution:
    """Résumé d'une distribution échantillonnée."""

    mean: float
    median: float
    p10: float
    p90: float
    std: float

    @classmethod
    def from_samples(cls, x: np.ndarray) -> Distribution:
        return cls(
            mean=float(np.mean(x)),
            median=float(np.median(x)),
            p10=float(np.percentile(x, 10)),
            p90=float(np.percentile(x, 90)),
            std=float(np.std(x)),
        )

    def to_dict(self) -> dict:
        return {
            "mean": round(self.mean, 2),
            "median": round(self.median, 2),
            "p10": round(self.p10, 2),
            "p90": round(self.p90, 2),
            "std": round(self.std, 2),
        }


@dataclass(frozen=True)
class ROIResult:
    fte_saved: Distribution
    annual_savings: Distribution
    net_benefit: Distribution
    roi_ratio: Distribution  # ROI = bénéfice net / budget
    payback_years: Distribution
    prob_roi_positive: float
    n_simulations: int

    def to_dict(self) -> dict:
        return {
            "n_simulations": self.n_simulations,
            "prob_roi_positive": round(self.prob_roi_positive, 4),
            "fte_saved": self.fte_saved.to_dict(),
            "annual_savings_eur": self.annual_savings.to_dict(),
            "net_benefit_eur": self.net_benefit.to_dict(),
            "roi_ratio": self.roi_ratio.to_dict(),
            "payback_years": self.payback_years.to_dict(),
        }


def _maturity_realization_mode(maturity_norm: np.ndarray) -> np.ndarray:
    """Mode de la fraction réalisable en fonction de la maturité normalisée [0,1].

    Affine : 25 % de réalisation à maturité nulle, 85 % à maturité maximale.
    Une organisation immature capte peu du potentiel d'automatisation théorique.
    """
    return np.clip(0.25 + 0.60 * maturity_norm, 0.0, 1.0)


def simulate_roi(
    inputs: ROIInputsResolved,
    n_simulations: int = 20_000,
    seed: int = 42,
) -> ROIResult:
    """Lance la simulation de Monte Carlo et renvoie les distributions.

    ``seed`` est fixé par défaut pour la **reproductibilité** (exigence mémoire).
    """
    rng = np.random.default_rng(seed)
    n = n_simulations

    # 1. Maturité incertaine : échantillonnage triangulaire du TFN global [0,4]
    a, m, b = inputs.maturity_tfn
    a, b = min(a, m), max(b, m)
    if b - a < 1e-9:
        maturity = np.full(n, m)
    else:
        maturity = rng.triangular(a, m, b, size=n)
    maturity_norm = np.clip(maturity / 4.0, 0.0, 1.0)

    # 2. Fraction réalisable : mode piloté par la maturité, dispersion par fiabilité
    spread = _RELIABILITY_SPREAD.get(inputs.measured_gains or "", _DEFAULT_SPREAD)
    mode = _maturity_realization_mode(maturity_norm)
    left = np.clip(mode - spread, 0.0, 1.0)
    right = np.clip(mode + spread, 0.0, 1.0)
    # garantir left < mode < right pour la loi triangulaire
    left = np.minimum(left, mode - 1e-6)
    right = np.maximum(right, mode + 1e-6)
    realizable = rng.triangular(left, mode, right)
    realizable = np.clip(realizable, 0.0, 1.0)

    # 3. ETP économisés et gains bruts
    annual_hours = inputs.hours_per_week * WEEKS_PER_YEAR
    fte_saved = annual_hours * realizable / HOURS_PER_FTE_YEAR
    annual_savings = fte_saved * inputs.cost_per_fte

    # 4. Provision de risque IA (fraction du budget)
    rl, rm, rr = _RISK_PROVISION.get(inputs.risk_cost or "", _DEFAULT_RISK)
    risk_fraction = rng.triangular(rl, rm, rr, size=n)
    risk_cost = risk_fraction * inputs.ai_budget

    # 5. Bénéfice net et ROI
    net_benefit = annual_savings - inputs.ai_budget - risk_cost
    budget = max(inputs.ai_budget, 1e-9)
    roi_ratio = net_benefit / budget

    # Payback (années) : budget / gains bruts, borné pour la lisibilité
    with np.errstate(divide="ignore", invalid="ignore"):
        payback = np.where(annual_savings > 0, inputs.ai_budget / annual_savings, np.inf)
    payback = np.clip(payback, 0.0, 50.0)

    return ROIResult(
        fte_saved=Distribution.from_samples(fte_saved),
        annual_savings=Distribution.from_samples(annual_savings),
        net_benefit=Distribution.from_samples(net_benefit),
        roi_ratio=Distribution.from_samples(roi_ratio),
        payback_years=Distribution.from_samples(payback),
        prob_roi_positive=float(np.mean(net_benefit > 0)),
        n_simulations=n,
    )


def build_roi_inputs(assessment_roi, maturity_tfn: tuple[float, float, float]) -> ROIInputsResolved:
    """Construit les entrées de simulation depuis les réponses ROI + la maturité.

    Args:
        assessment_roi: instance de :class:`maturai.domain.responses.ROIInputs`.
        maturity_tfn: ``(a, m, b)`` du TFN de score global.
    """
    return ROIInputsResolved(
        hours_per_week=assessment_roi.hours_per_week,
        cost_per_fte=assessment_roi.cost_per_fte,
        ai_budget=assessment_roi.ai_budget,
        n_automatable_tasks=assessment_roi.n_automatable_tasks,
        measured_gains=assessment_roi.measured_gains,
        risk_cost=assessment_roi.risk_cost,
        maturity_tfn=maturity_tfn,
    )
