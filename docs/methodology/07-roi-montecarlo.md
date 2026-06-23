# 07 — ROI / ETP par simulation de Monte Carlo

## Pourquoi Monte Carlo

Un ROI ponctuel est faussement précis. On simule des milliers de scénarios en
échantillonnant les paramètres incertains et on restitue une **distribution** :
ROI médian, intervalle P10–P90, probabilité que le ROI soit positif. La
simulation **consomme directement le score de maturité et son incertitude** (le
TFN global) — brique 6 ← brique 3.

## Modèle (volontairement simple et justifié)

| Étape | Formule |
|-------|---------|
| Heures annuelles sur tâches automatisables | `H = hours_per_week × 47` |
| Fraction réalisable `r` | loi triangulaire, **mode piloté par la maturité** : `0,25 + 0,60·maturité_norm` ; dispersion pilotée par la fiabilité déclarée (Q41) |
| ETP économisés | `FTE = H · r / 1600` |
| Gains bruts annuels | `G = FTE · cost_per_fte` |
| Provision de risque IA (Q43) | fraction du budget, échantillonnée |
| Bénéfice net | `N = G − ai_budget − risque` |
| ROI | `N / ai_budget` ; payback `ai_budget / G` |

Une organisation **peu mature ne capte qu'une faible part** du potentiel
théorique d'automatisation : c'est ce que traduit le couplage maturité → mode de
`r`. Toutes les constantes (47 semaines, 1600 h/ETP, provisions de risque) sont
**documentées et ajustables** dans `roi/monte_carlo.py`.

## Variables d'entrée (Q38–Q43)

| Question | Variable | Usage |
|----------|----------|-------|
| Q38 | nb tâches automatisables | contexte / cadrage |
| Q39 | heures/semaine sur ces tâches | base du calcul ETP |
| Q40 | coût chargé d'un ETP | conversion ETP → € |
| Q41 | gains déjà mesurés ? | **dispersion** de `r` (fiabilité) |
| Q42 | budget IA annuel | dénominateur du ROI |
| Q43 | coût du risque IA chiffré ? | **provision** soustraite |

## Sorties (`ROIResult`)

Distributions (moyenne, médiane, P10, P90, écart-type) de : ETP économisés, gains
annuels, bénéfice net, ratio ROI, délai de retour ; plus `P(ROI > 0)`.

## Reproductibilité

`seed` fixé par défaut (exigence mémoire) ; vérifié par `tests/test_roi.py`
(mêmes entrées + même graine → mêmes statistiques ; maturité ↑ → gains ↑).
