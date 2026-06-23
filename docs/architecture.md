# Architecture technique

## Vue d'ensemble

Le système est organisé en **couches** dont la dépendance est strictement
descendante : chaque couche ne connaît que celles du dessous, jamais l'inverse.
Cela garantit que le cœur scientifique (scoring) reste **pur et testable**,
indépendant de l'IA générative, du graphe et de l'interface.

```
maturai/
├── domain/        ← modèles purs : Referential, Assessment, TFN
│                     (aucune dépendance interne ; tout en dépend)
├── referential/   ← chargement + validation du référentiel (dépend de domain)
├── weighting/     ← Fuzzy AHP (dépend de domain)
├── scoring/       ← MOTEUR : fuzzification, agrégation, inférence, défuzzif.
│                     (dépend de domain, weighting)
├── roi/           ← Monte Carlo (dépend de domain ; consomme un score)
├── validation/    ← profils simulés + comparaison (dépend de scoring)
├── graphrag/      ← Neo4j + LlamaIndex + mock (interfaces ; dépend de domain)
├── reporting/     ← rapport LLM (dépend de scoring/results)
└── anfis/         ← neuro-flou (interface ; à entraîner)
```

## Pourquoi cette séparation

- **Testabilité** : `scoring` ne fait aucun appel réseau → tests déterministes
  rapides (`pytest`), conformément à l'exigence « tester le moteur isolément ».
- **Substituabilité** : `graphrag` et `reporting` sont derrière des interfaces
  (`Protocol`). Le mock et le réel sont interchangeables sans toucher au reste.
- **Traçabilité scientifique** : chaque hyperparamètre vit dans `config.py`
  (`ScoringConfig`), donc explicite et variable dans le protocole de validation.

## Flux de données (une évaluation)

```
questions.json ──load──► Referential ─┐
                                       ├─► score_assessment() ─► AssessmentScore ─┬─► ROI Monte Carlo
Assessment (réponses) ─────────────────┘        ▲                                  └─► build_report_prompt ─► LLM
                                                 │
                          Fuzzy AHP (poids d'axes)│
                                                 │
Graph-RAG (preuves) ─► confidence des réponses ──┘   (étape 5 : module la fuzzification)
```

## Le pipeline de scoring en détail

`score_assessment` (dans `scoring/engine.py`) enchaîne :

1. `_resolve_axis_weights` — Fuzzy AHP (repli sur poids du référentiel).
2. Par question : `fuzzify_response` → TFN (incertitude injectée).
3. `aggregate` (moyenne pondérée floue) : question → sous-domaine → axe → global.
4. `defuzzify` (centroïde) des TFN d'axes → scores crisp.
5. `infer_incoherence_penalty` (Mamdani) sur les scores d'axes crisp.
6. Score global final = global brut − pénalité, borné `[0,4]`.
7. `_classic_weighted_mean` calculé en parallèle (baseline de comparaison).

Sortie : `AssessmentScore` (sérialisable via `to_dict()`), consommé par `roi`,
`reporting` et l'interface web.

## Dépendances externes et extras

| Extra | Paquets | Utilisé par |
|-------|---------|-------------|
| (cœur) | numpy, scipy, pydantic, jsonschema | domain, referential, weighting, scoring, roi, validation |
| `fuzzy` | scikit-fuzzy, torch | anfis, comparaison Mamdani de référence |
| `graphrag` | neo4j, llama-index | graphrag (étape 5) |
| `report` | anthropic, jinja2 | reporting (étape 6) |

Le cœur fonctionne **sans aucun extra**.
