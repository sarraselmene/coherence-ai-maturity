# 02 — Moteur de scoring flou (Mamdani hiérarchique)

## Pourquoi la logique floue

Une réponse organisationnelle réelle se situe **rarement strictement à un
niveau**, mais dans une zone intermédiaire entre deux niveaux adjacents. La
logique floue représente chaque grandeur par un **degré d'appartenance** à
plusieurs niveaux, propage cette nuance dans l'agrégation, et ne la réduit qu'à
la toute fin (défuzzification). C'est l'alternative rigoureuse à l'agrégation
linéaire (moyenne pondérée) des frameworks commerciaux.

## Fonctions d'appartenance (`scoring/membership.py`)

Sur l'univers `[0,4]`, 5 MF triangulaires, sommets aux entiers 0..4 :

```
µ
1 ┤ █0    █1    █2    █3    █4
  │ ╱ ╲  ╱ ╲  ╱ ╲  ╱ ╲  ╱ ╲
0 ┼█───╳────╳────╳────╳───█──► score
  0    1    2    3    4
```

**Partition de l'unité** : en tout point, la somme des degrés vaut 1, et au plus
deux niveaux adjacents sont actifs. Un score 2,4 = {Défini : 0,6 ; Géré : 0,4}.

## Pipeline (`scoring/engine.py`)

### 1. Fuzzification (`scoring/fuzzification.py`)
Réponse crisp `k` → `TFN(k − s, k, k + s)` borné `[0,4]`, avec
`s = base_spread + (1 − confidence) · max_extra_spread`. L'incertitude entre
**dès l'entrée** (cf. [04-uncertainty](04-uncertainty.md)).

### 2. Agrégation hiérarchique floue (`scoring/aggregation.py`)
Moyenne pondérée floue, niveau par niveau :
```
score(noeud) = ( Σ_i  w_i ⊗ TFN_i ) ⊘ ( Σ_i w_i )
```
appliquée questions → sous-domaines → axes → global. Contrairement à la moyenne
arithmétique, l'opérateur flou **conserve et compose les largeurs** des TFN.

### 3. Défuzzification des axes (`scoring/defuzzification.py`)
Centroïde des TFN d'axes → scores crisp `[0,4]`, requis par l'inférence Mamdani.

### 4. Inférence Mamdani inter-axes (`scoring/inference.py`)
C'est la pièce que l'agrégation linéaire ne sait pas faire : modéliser les
**incohérences entre dimensions**.

- Termes linguistiques par axe : `LOW (0,0,2)`, `MED (1,2,3)`, `HIGH (2,4,4)`.
- Règles (`scoring/rules/incoherence_rules.py`), toutes de type *écart* :
  | Règle | Antécédent | Conséquent |
  |-------|------------|------------|
  | ambition_sans_gouvernance | (Stratégie HAUT **ou** Techno HAUT) **et** Gouvernance BAS | pénalité LARGE |
  | deploiement_sur_donnees_faibles | Techno HAUT **et** Données BAS | pénalité MEDIUM |
  | ambition_sans_talents | Stratégie HAUT **et** Talents BAS | pénalité MEDIUM |
- Mécanique Mamdani : force `α_r = min/max` des antécédents → écrêtage du
  conséquent à `α_r` (implication min) → agrégation par max → **centroïde** →
  pénalité crisp ∈ `[0,1]`.

> Choix de conception : un profil **uniformément bas** n'est pas une incohérence
> (c'est de la faible maturité, déjà reflétée par le score). Toutes les règles
> exigent donc un axe HAUT **face à** un axe BAS.

### 5. Score final
`global = défuzz(global_TFN) − pénalité`, borné `[0,4]`, puis présenté `+1` sur
`[1,5]`. On expose aussi un **intervalle de crédibilité** (coupe-α du TFN global).

## Implémentation

Le cœur (TFN, agrégation, Mamdani) est implémenté en numpy pur (`domain`,
`scoring`) — exact, testable, sans dépendance lourde. `scikit-fuzzy` reste
disponible (extra `fuzzy`) comme implémentation Mamdani **de référence** pour
recouper les résultats dans le mémoire.

## Test isolé (exigence étape 2)

`tests/test_engine.py` valide le moteur sur des profils fictifs **sans interface
ni LLM** : profils cohérents (écart flou-classique ≈ 0), profils incohérents
(score flou < classique, incohérences signalées), bornes `[0,4]`/`[1,5]`.
