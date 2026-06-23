# 01 — Le référentiel : double ancrage et traçabilité

## Principe : double ancrage méthodologique

Chaque dimension repose sur **deux couches** :

1. **Ancrage générique** — un référentiel reconnu qui structure la dimension *en
   principe* :
   - Stratégie, Talents, Technologie → **PwC AI Maturity Assessment** + **McKinsey State of AI** ;
   - Données → **DAMA-DMBOK** ;
   - Gouvernance → **ISO/IEC 42001**.
2. **Couche IA-spécifique** — ce que les référentiels génériques ne couvrent pas,
   propre à l'IA : biais algorithmique, traçabilité des données d'entraînement,
   risques LLM, classification réglementaire → **NIST AI RMF**, **EU AI Act**,
   données empiriques **McKinsey**.

Dans `questions.json`, chaque question porte :
- `layer` : `generic` ou `ai_specific` (matérialise les deux couches) ;
- `referential.sources` : la/les source(s) ;
- `referential.justification` : *pourquoi* cette question relève de cette source.

C'est ce qui rend chaque question **explicitement justifiable** — réponse directe
à la critique des grilles propriétaires dont la notation reste non publiée.

## Structure

```
Référentiel
├── meta (échelle, libellés de niveaux, sources, méthode de pondération)
├── context_section  (Q1–Q6, hors scoring : secteur, taille, rôle…)
├── axes[5]
│   └── subdomains[]
│       └── questions[]  (5 modalités 0–4, layer, traçabilité, indice Graph-RAG)
└── roi_module  (Q38–Q43, hors scoring : variables factuelles ROI)
```

## Couverture (double ancrage chiffré)

| Axe | Total | Génériques | IA-spécifiques |
|-----|-------|------------|----------------|
| Stratégie | 6 | 6 | 0 |
| Données | 8 | 6 | 2 (Q15bis biais, Q18bis lineage) |
| Talents | 5 | 5 | 0 |
| Technologie | 4 | 4 | 0 |
| Gouvernance | 10 | 3 | 7 (Q31–Q37) |

> ⚠️ Données passe de 6 à 8 questions par intégration de la couche IA-spécifique
> (cf. [DESIGN_DECISIONS P1](../DESIGN_DECISIONS.md)). Poids d'axe maintenu à 20 %.

## Garde-fous (validation à deux niveaux)

- **Structurelle** (jsonschema, `schema/questions.schema.json`) : forme du JSON,
  5 niveaux exactement, types.
- **Sémantique** (`referential/validators.py`) : identifiants uniques, poids > 0,
  sources connues, niveaux strictement `0..4`, couverture des axes.

Échouer tôt et clairement : le référentiel étant le socle, aucune brique aval ne
démarre sur une base douteuse.

## Modalités 0–4

Les 5 modalités sont des **ancres comportementales** (pas de simples « oui/non »),
calquées sur la progression CMMI : 0 Initial → 1 Émergent → 2 Défini → 3 Géré →
4 Optimisé. Exemple (Q7, présence de l'IA dans le plan stratégique) :

| Score | Ancre |
|-------|-------|
| 0 | Absente de toute réflexion stratégique |
| 1 | Évoquée informellement, sans document |
| 2 | Mentionnée dans la stratégie globale, sans plan dédié |
| 3 | Plan IA formalisé, mais non chiffré ni daté |
| 4 | Plan IA formalisé, daté et chiffré sur 3 ans |

Ces ancres rendent la réponse **objectivable** et corroborables par le Graph-RAG.
