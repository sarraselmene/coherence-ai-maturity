# 03 — ANFIS (système d'inférence neuro-flou adaptatif)

## Limite levée

Le moteur Mamdani (étape 2) utilise des fonctions d'appartenance et des règles
**fixées à la main**. L'ANFIS les rend **apprenables** depuis des données, tout
en restant interprétable (Takagi-Sugeno différentiable, pas une boîte noire).

Position dans la chaîne : `Fuzzy AHP (poids) → ANFIS (MF/règles) → score + incertitude`.
L'ANFIS raffine le mapping *réponses d'un axe → score d'axe* ; les poids
inter-axes restent fournis par le Fuzzy AHP.

## Architecture cible (5 couches, Sugeno ordre 1)

1. **Fuzzification** : MF gaussiennes apprenables `(c, σ)` par entrée.
2. **Règles** : force d'activation `wᵢ = Π µ` (produit des degrés).
3. **Normalisation** : `w̄ᵢ = wᵢ / Σ wⱼ`.
4. **Conséquents** : `fᵢ = pᵢ·x + qᵢ·y + … + rᵢ` (linéaires).
5. **Sortie** : `Σ w̄ᵢ·fᵢ`.

Apprentissage **hybride** : moindres carrés (conséquents) + descente de gradient
(prémisses), ou Adam de bout en bout (PyTorch, extra `fuzzy`).

## Données d'entraînement (sans historique client)

1. **Distillation du moteur Mamdani** : l'ANFIS apprend d'abord à reproduire le
   moteur de l'étape 2 (cible = scores Mamdani sur profils simulés), garantissant
   une base de comparaison et un *warm start* interprétable.
2. **Étiquetage expert** de profils simulés (`validation.profiles`) pour affiner.

## Garde-fous

- Contraindre `σ > 0` et l'ordre des centres pour préserver la lisibilité des MF.
- Régularisation + validation croisée pour éviter le surapprentissage sur peu de
  données.
- Comparaison systématique classique / Mamdani / ANFIS (cf. [05](05-validation.md))
  pour vérifier que la complexité supplémentaire **apporte** réellement.

## Statut : implémenté

`maturai.anfis.ANFIS` est un réseau Takagi-Sugeno différentiable (PyTorch, extra
`fuzzy`) à MF gaussiennes apprenables et conséquents linéaires, API `fit`/`predict`.

`maturai.anfis.training.train_global_anfis` réalise la **distillation** du moteur
flou (axes → score global). Résultat mesuré (300 profils de test) :
**MAE ≈ 0,05, corrélation ≈ 0,997**. La comparaison à trois scorings
(`scripts/run_anfis.py`) montre que, sur les profils incohérents, l'ANFIS **chute
comme le moteur flou** (score ~1,4–1,7) là où le scoring classique reste à ~2,2 :
l'ANFIS a appris la pénalité d'incohérence **à partir des seules données**.

Étape suivante : ré-entraînement/affinage sur des labels experts réels lorsqu'ils
seront disponibles (le warm-start par distillation est déjà en place).
