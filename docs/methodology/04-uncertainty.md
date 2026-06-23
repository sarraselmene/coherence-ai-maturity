# 04 — Propagation d'incertitude (nombres flous triangulaires)

## Idée

Un score « 3,2 / 5 » présenté comme exact est trompeur. MaturAI porte
l'**incertitude de bout en bout** : chaque grandeur est un nombre flou
triangulaire `TFN(a, m, b)` et l'agrégation propage les largeurs au lieu de les
écraser. La sortie n'est pas un point mais un **intervalle de crédibilité**.

## Sources d'incertitude injectées à la fuzzification

`s = base_spread + (1 − confidence) · max_extra_spread`

- `base_spread` (= 0,5) : incertitude **irréductible** — même une réponse assumée
  approxime une réalité nuancée (fondement méthodologique du sujet) ;
- terme en `(1 − confidence)` : incertitude **de fiabilité** — réponse non
  corroborée par le Graph-RAG, répondant peu légitime, désaccord entre parties
  prenantes → support plus large.

C'est le **point de jonction avec le Graph-RAG** (brique 5 → brique 3) : une
preuve documentaire qui contredit la réponse abaisse `confidence`, donc élargit
le TFN, donc accroît l'incertitude affichée.

## Arithmétique (`domain/fuzzy_number.py`)

Sur grandeurs positives (scores, poids), formes fermées :
- addition `(a₁+a₂, m₁+m₂, b₁+b₂)` ;
- produit `(a₁a₂, m₁m₂, b₁b₂)` ; quotient `(a₁/b₂, m₁/m₂, b₁/a₂)` ;
- moyenne pondérée floue `(Σ wᵢ⊗xᵢ) ⊘ (Σ wᵢ)`.

Propriété vérifiée par test : l'agrégation de grandeurs incertaines reste
incertaine (`width > 0`), là où une moyenne classique renverrait un point sec.

## Sorties d'incertitude

- **Coupe-α** `[a + α(m−a), b − α(b−m)]` → intervalle de crédibilité du score
  global (α = 0,5 par défaut).
- **Largeur du support** par axe → indicateur scalaire d'incertitude, affiché
  dans le rapport (`±` par axe).

## Consommation par le ROI

Le module Monte Carlo (brique 6) **échantillonne** le TFN de score global
(loi triangulaire sur `[a, m, b]`) : l'incertitude du score devient une source de
variabilité du ROI, propagée jusqu'aux distributions financières (cf. [07](07-roi-montecarlo.md)).

## Limite et calibration

Les hyperparamètres `base_spread`/`max_extra_spread` sont à **calibrer** (analyse
de sensibilité dans le protocole de validation, ou avis d'experts) — cf.
[DESIGN_DECISIONS P3](../DESIGN_DECISIONS.md).
