# MaturAI — Outil d'évaluation de la maturité IA (KPMG)

> Outil d'évaluation de la maturité IA des organisations, fondé sur un référentiel
> **traçable et reproductible**, un moteur de scoring **neuro-flou avec propagation
> d'incertitude**, un module **ROI Monte Carlo**, et un pipeline d'extraction de
> preuves **Graph-RAG (Neo4j + LlamaIndex)**.

Ce dépôt est le support technique d'un mémoire d'ingénieur. Chaque choix de
conception est **explicitement justifié** dans [`docs/methodology/`](docs/methodology/)
et tracé jusqu'à sa source académique ou normative.

---

## 1. Pourquoi cet outil se distingue des grilles propriétaires

Les grilles de maturité IA des cabinets de conseil partagent trois limites :

1. **Méthodologie de notation non publiée** → résultats non reproductibles.
2. **Agrégation linéaire simple** (moyenne pondérée) → masque les incohérences
   inter-dimensions (ex. stratégie ambitieuse + gouvernance défaillante).
3. **Aucune gestion de l'incertitude** → un score « 3,2 / 5 » est présenté comme
   exact alors que la réalité organisationnelle est floue.

MaturAI répond à ces trois limites :

| Limite des grilles propriétaires | Réponse de MaturAI | Référence |
|---|---|---|
| Notation opaque | Référentiel à double ancrage, chaque question tracée à sa source | [`01-referential.md`](docs/methodology/01-referential.md) |
| Pondération arbitraire | **Fuzzy AHP** calibré par comparaisons par paires (cohérence vérifiée) | [`02-fuzzy-ahp.md`](docs/methodology/02-fuzzy-ahp.md) |
| Notation fixée à la main | **ANFIS** : fonctions d'appartenance et règles apprises | [`03-anfis.md`](docs/methodology/03-anfis.md) |
| Score ponctuel faussement exact | **Propagation d'incertitude** (nombres flous triangulaires bout en bout) | [`04-uncertainty.md`](docs/methodology/04-uncertainty.md) |
| Agrégation linéaire aveugle aux incohérences | **Inférence Mamdani** + règles d'incohérence inter-axes | [`02-fuzzy-scoring.md`](docs/methodology/02-fuzzy-scoring.md) |
| Pas de validation | **Protocole quantitatif** : classique vs flou vs neuro-flou | [`05-validation.md`](docs/methodology/05-validation.md) |

---

## 2. Architecture en couches

```
                ┌─────────────────────────────────────────────────┐
   Couche 4     │  Reporting LLM : synthèse narrative + KPI suivi  │
   (rapport)    └─────────────────────────────────────────────────┘
                                     ▲
                ┌─────────────────────────────────────────────────┐
   Couche 3     │  ROI Monte Carlo  ·  consomme score + incertitude │
   (décision)   └─────────────────────────────────────────────────┘
                                     ▲
                ┌─────────────────────────────────────────────────┐
   Couche 2     │  MOTEUR DE SCORING                                │
   (cœur        │   Fuzzy AHP (poids) → Fuzzification (TFN) →       │
    scientifique)│   Agrégation hiérarchique → Inférence Mamdani    │
                │   (règles d'incohérence) → Défuzzification        │
                │   + ANFIS (MF/règles apprises) + propagation      │
                │   d'incertitude (TFN bout en bout)                │
                └─────────────────────────────────────────────────┘
                          ▲                              ▲
        ┌─────────────────┴──────┐        ┌──────────────┴──────────────┐
   C.1  │  Référentiel figé      │        │  Graph-RAG (Neo4j+LlamaIndex)│
 (socle)│  questions.json tracé  │        │  extraction de preuves +     │
        │  vers PwC/DAMA/ISO/    │        │  détection d'incohérences →  │
        │  NIST/EU AI Act/McK.   │        │  alimente le score de        │
        │                        │        │  confiance                   │
        └────────────────────────┘        └──────────────────────────────┘
```

Détail complet : [`docs/architecture.md`](docs/architecture.md).

---

## 3. Correspondance feuille de route ↔ modules

| Étape | Objet | Module | Statut |
|---|---|---|---|
| 1 | Référentiel figé | [`data/referential/`](data/referential/) + `maturai.referential` | ✅ implémenté |
| 2 | Moteur fuzzy (Mamdani hiérarchique) | `maturai.scoring` | ✅ implémenté |
| 1b | Pondération inter-axes (Fuzzy AHP) | `maturai.weighting` | ✅ implémenté |
| 3 | Propagation d'incertitude (TFN) | `maturai.scoring` (TFN bout en bout) | ✅ implémenté |
| 3b | Protocole de validation | `maturai.validation` | ✅ profils + campagne massive + comparaison 3 scorings |
| 2b | ANFIS (MF/règles apprises) | `maturai.anfis` | ✅ implémenté (PyTorch) + distillation (corr ≈ 0,997) |
| 4 | ROI Monte Carlo | `maturai.roi` | ✅ implémenté |
| 5 | Graph-RAG | `maturai.graphrag` | ◑ réconciliation testée + ingestion/extraction Neo4j+LlamaIndex prêtes (requiert Docker) |
| 6 | Rapport LLM | `maturai.reporting` | ◷ interface + prompt structuré (appel LLM = clé API) |
| 7 | Interface web | (à trancher) | ⏳ étape 7 |

Légende : ✅ fonctionnel et testé · ◑ partiel · ◷ contrat défini + stub documenté · ⏳ à venir.

---

## 4. Installation

Prérequis : **Python 3.11+** (le `python` du Windows Store ne suffit pas — installer
depuis [python.org](https://www.python.org/downloads/)). Docker Desktop est requis
uniquement pour le Graph-RAG (étape 5).

```powershell
# Depuis la racine du projet
./scripts/setup.ps1            # crée le venv et installe les dépendances
# ou manuellement :
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## 5. Démarrage rapide

```powershell
.\.venv\Scripts\Activate.ps1

# Démo de bout en bout (référentiel → AHP → fuzzy → ROI → Graph-RAG mock → prompt)
python scripts/run_scoring_demo.py

# Campagne de validation : flou vs classique sur N profils (figure + CSV dans outputs/)
python scripts/run_validation.py 500

# ANFIS : entraînement par distillation + comparaison 3 scorings (requiert l'extra fuzzy)
python scripts/run_anfis.py

# Graph-RAG réel (requiert Docker + clés API)
docker compose up -d ; python scripts/build_graph.py

# Tests
pytest -q
```

## 6. Structure du dépôt

```
.
├── data/
│   ├── referential/        # questions.json (LE référentiel) + schéma JSON
│   ├── weights/            # matrices de comparaison par paires (Fuzzy AHP)
│   ├── profiles/           # profils d'entreprises simulés (validation)
│   └── corpus/             # documents fictifs pour le Graph-RAG (étape 5)
├── docs/
│   ├── architecture.md
│   ├── DESIGN_DECISIONS.md # journal des décisions + points ouverts
│   └── methodology/        # justification scientifique de chaque brique
├── src/maturai/            # le package Python
│   ├── domain/             # modèles métier + nombres flous triangulaires
│   ├── referential/        # chargement + validation du référentiel
│   ├── weighting/          # Fuzzy AHP
│   ├── scoring/            # moteur flou (cœur)
│   ├── anfis/              # neuro-flou (interface + plan)
│   ├── roi/                # Monte Carlo
│   ├── graphrag/           # Neo4j + LlamaIndex (interface + mock)
│   ├── reporting/          # rapport LLM (interface)
│   └── validation/         # profils simulés + comparaison
├── tests/
└── scripts/
```

## 7. Conventions

- **Échelle interne** : scores continus dans `[0, 4]` (cohérent avec les 5 modalités
  0–4 des questions). **Échelle présentée** : niveau dans `[1, 5]` = score + 1
  (cohérent avec le modèle CMMI 1–5). Voir [`docs/methodology/00-overview.md`](docs/methodology/00-overview.md).
- Toute incertitude est portée par un **nombre flou triangulaire** `TFN(a, m, b)`
  où `a ≤ m ≤ b` (support, mode, support).

---

🤖 Échafaudage généré avec [Claude Code](https://claude.com/claude-code)
