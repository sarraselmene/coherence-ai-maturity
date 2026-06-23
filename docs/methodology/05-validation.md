# 05 — Protocole de validation quantitative

> À mener **tôt**, pas en fin de projet : c'est l'argument scientifique central
> du mémoire (la démonstration que le moteur flou apporte quelque chose que
> l'agrégation linéaire n'apporte pas).

## Démarche

En l'absence d'historique client, on valide sur des **profils simulés** dont on
connaît *a priori* le comportement attendu (`maturai.validation.profiles`) :

- **profils cohérents** (tous les axes au même niveau) : le moteur flou doit y
  produire un score **proche** de la moyenne classique (rien à pénaliser) ;
- **profils incohérents** (axes contradictoires) : le moteur flou doit y produire
  un score **plus bas** et **signaler** l'incohérence.

## Comparaison à trois scorings

| Scoring | Statut | Module |
|---------|--------|--------|
| Classique (moyenne pondérée hiérarchique) | ✅ baseline | `engine._classic_weighted_mean` |
| Flou (Mamdani hiérarchique + TFN) | ✅ | `scoring.engine` |
| Neuro-flou (ANFIS) | ✅ implémenté (distillation) | `anfis` |

`validation/compare.py` calcule pour chaque profil : score classique, score
flou, écart, pénalité, nombre d'incohérences ; `summarize()` agrège l'écart moyen
sur profils cohérents vs incohérents. La comparaison à trois scorings tourne via
`scripts/run_anfis.py` (résultat : sur profils incohérents, flou et ANFIS ~1,4–1,7
vs classique ~2,2).

## Campagne massive (`validation/campaign.py`)

`run_campaign()` génère des centaines de profils aléatoires ; on mesure l'écart
`flou − classique` en fonction de l'**incohérence inter-axes** (étendue
`max − min` des niveaux). Résultat empirique (`scripts/run_validation.py`,
400 profils) : **corrélation ≈ −0,31**, écart moyen passant de ~0 (cohérents) à
**−0,37** (très incohérents) — la pénalité floue croît de façon monotone avec
l'incohérence. Figure + CSV générés dans `outputs/`.

## Hypothèse testée (et vérifiée par les tests)

> `mean_gap_incoherent < mean_gap_coherent` et `mean_penalty_incoherent > 0`.

Autrement dit : l'écart flou−classique est **significativement plus négatif** sur
les profils incohérents. C'est le résultat à présenter (tableau + graphe) dans le
chapitre validation. Voir `tests/test_validation.py`.

## Extensions prévues

1. **Génération massive** de profils (grille + bruit gaussien `jitter`) pour des
   statistiques robustes (distribution des écarts, et non quelques points).
2. **Analyse de sensibilité** aux hyperparamètres (`base_spread`,
   `incoherence_strength`, poids AHP) : robustesse des conclusions.
3. **Branchement ANFIS** : une fois entraîné, il se compare via la même interface
   `compare_profiles` (étendue à 3 colonnes).
4. **Concordance experte** (si données disponibles) : corrélation score moteur ↔
   notation d'experts (Spearman / κ pondéré).
