# 02-ahp — Pondération inter-axes par Fuzzy AHP

## Problème

Combien pèse chaque axe dans le score global ? Les grilles commerciales imposent
des poids **sans justification**. On les **dérive** ici de comparaisons par
paires d'experts, méthode auditée et reproductible (`maturai.weighting`).

## AHP classique → Fuzzy AHP

L'AHP (Saaty) élicite des jugements « l'axe A est *x* fois plus important que B »
sur l'échelle 1–9. Limite : un jugement crisp suppose une précision irréaliste.
Le **Fuzzy AHP** remplace chaque jugement par un **TFN** (tolérance autour du
jugement) :

- `1 → (1,1,1)` ; `x → (x−1, x, x+1)` ; `1/x → (1/(x+1), 1/x, 1/(x−1))`.

## Méthode de Chang (analyse des étendues)

1. **Étendue synthétique floue** de l'axe *i* :
   `S_i = (Σ_j M_ij) ⊗ (Σ_i Σ_j M_ij)^{-1}` (TFN).
2. **Poids** : deux variantes calculées :
   - **faisant foi** — centroïde de `S_i`, normalisé : toujours > 0 (robuste) ;
   - **comparatif** — degré de possibilité `V(S_i ≥ S_k)` puis min (Chang
     d'origine) : peut produire des zéros (limite connue), conservé pour
     discussion.

> Choix (D4) : on retient les **centroïdes normalisés** pour ne jamais annuler
> un axe ; les poids de Chang restent affichés à titre de comparaison.

## Cohérence des jugements (`weighting/consistency.py`)

Une matrice n'a de valeur que si elle est cohérente. On calcule le **ratio de
cohérence** de Saaty :
`CI = (λ_max − n)/(n − 1)`, `CR = CI / RI(n)`. Seuil d'acceptation : `CR ≤ 0,10`.

## Matrice utilisée (`data/weights/ahp_pairwise.json`)

Jugements calibrés pour refléter la priorité risque/réglementaire (Gouvernance)
tout en restant cohérents avec le récapitulatif initial :

| | Strat | Données | Talents | Techno | Gouv |
|--|--|--|--|--|--|
| Stratégie | 1 | 1 | 2 | 2 | 1/2 |
| Données | 1 | 1 | 2 | 2 | 1/2 |
| Talents | 1/2 | 1/2 | 1 | 1 | 1/3 |
| Technologie | 1/2 | 1/2 | 1 | 1 | 1/3 |
| Gouvernance | 2 | 2 | 3 | 3 | 1 |

**Poids obtenus** (centroïde) ≈ Stratégie 0,21 · Données 0,21 · Talents 0,11 ·
Technologie 0,11 · Gouvernance 0,35, avec `CR` bien en deçà de 0,10. Cohérent
avec la cible initiale (20/20/15/15/30), la Gouvernance ressortant légèrement
renforcée — ce qui se *justifie* par jugements, là où la cible était posée à dire d'expert.

## Articulation avec le reste

Les poids d'axes alimentent l'agrégation globale (`scoring/engine.py`). Les poids
de sous-domaines/questions restent équipondérés par défaut (cf.
[DESIGN_DECISIONS P2](../DESIGN_DECISIONS.md)).
