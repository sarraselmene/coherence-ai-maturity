# 00 — Vue d'ensemble méthodologique

## Problème

Évaluer la maturité IA d'une organisation sur une échelle 1–5 (inspirée CMMI),
de façon **reproductible, traçable et honnête sur l'incertitude** — à l'inverse
des grilles propriétaires (notation opaque, agrégation linéaire non justifiée,
score ponctuel faussement exact).

## Chaîne méthodologique enrichie

```
1. Fuzzy AHP        → poids inter-axes calibrés par comparaisons par paires
        ↓ alimente
2. ANFIS            → fonctions d'appartenance + règles apprises (pas fixées à la main)
        ↓ produit
3. Score + incertitude → nombres flous triangulaires (TFN) propagés de bout en bout
        ↓ validé par
4. Validation       → profils simulés ; comparaison classique vs flou vs neuro-flou
        ↓ en parallèle
5. Graph-RAG        → extraction de preuves + détection d'incohérences → score de confiance
        ↓ en parallèle
6. ROI Monte Carlo  → consomme le score de maturité ET son incertitude
```

## Conventions transverses

- **Échelle interne** : score continu dans `[0,4]` (5 modalités 0–4).
- **Échelle présentée** : niveau dans `[1,5]` = score interne + 1.
- **Incertitude** : nombre flou triangulaire `TFN(a, m, b)`, `a ≤ m ≤ b`.
  Défuzzification systématique par **centroïde** `(a+m+b)/3`.

## Lien briques ↔ modules de code

| Brique | Module | Doc |
|--------|--------|-----|
| Référentiel | `maturai.referential` | [01](01-referential.md) |
| Fuzzy AHP | `maturai.weighting` | [02-ahp](02-fuzzy-ahp.md) |
| Moteur flou (Mamdani hiérarchique) | `maturai.scoring` | [02-scoring](02-fuzzy-scoring.md) |
| ANFIS | `maturai.anfis` | [03](03-anfis.md) |
| Propagation d'incertitude | `maturai.scoring` (TFN) | [04](04-uncertainty.md) |
| Validation | `maturai.validation` | [05](05-validation.md) |
| Graph-RAG | `maturai.graphrag` | [06](06-graphrag.md) |
| ROI Monte Carlo | `maturai.roi` | [07](07-roi-montecarlo.md) |
