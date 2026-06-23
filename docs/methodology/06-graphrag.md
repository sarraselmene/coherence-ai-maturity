# 06 — Graph-RAG : extraction de preuves & détection d'incohérences

## Rôle dans le système

En amont du questionnaire, analyser les documents internes du client pour
**suggérer des réponses** (validées ensuite par les parties prenantes) et
**détecter les écarts** entre réponse déclarée et preuve documentaire. Ces écarts
abaissent la `confidence` des réponses → élargissent leur TFN → nourrissent le
**score de confiance** et l'incertitude (jonction brique 5 → brique 3).

## Pourquoi Graph-RAG (et non RAG vectoriel simple)

Les preuves recherchées sont souvent **relationnelles** : « COMEX » relié à
« formation IA », « Charte IA » qui « couvre » « éthique IA ». Un graphe de
connaissances capture explicitement ces relations là où la similarité
vectorielle seule les manquerait. D'où **Neo4j + LlamaIndex `PropertyGraphIndex`**
(recherche hybride graphe + vecteur).

## Architecture (étape 5)

```
data/corpus/*.pdf ─► LlamaIndex readers ─► PropertyGraphIndex
                                                │ (extraction entités/relations par LLM)
                                                ▼
                                         Neo4jPropertyGraphStore  (docker-compose)
                                                │
question.target_entities ─► requête hybride ─► extrait + sous-graphe
                                                │ (LLM → modalité 0..4 + citation)
                                                ▼
                                         EvidenceSuggestion
```

## Contrats (`graphrag/interfaces.py`) — définis avant l'implémentation

- `EvidenceSuggestion(question_id, suggested_score, confidence, snippet, source, entities)`
- `EvidenceExtractor` (`Protocol`) : `suggest_for_question`, `suggest_all`.
- `detect_coherence(declared, evidence)` → `CoherenceFinding[]` (écarts > tolérance).

Le `MockEvidenceExtractor` respecte ce contrat : tout le pipeline (réconciliation,
confiance, pré-remplissage) se développe et se teste **sans Neo4j**. La bascule
vers `GraphRagEvidenceExtractor` ne touchera aucun code aval (D7).

## Corpus de démonstration

Documents fictifs cohérents à préparer dans `data/corpus/` : charte IA, rapport
d'audit, organigramme, politique data, etc. Axe prioritaire : **Gouvernance**
(le plus riche en entités et le plus discriminant).

## Prérequis d'exécution

`docker compose up -d` (Neo4j + APOC) puis `pip install -e ".[graphrag]"`.
Variables `NEO4J_*` et clés LLM/embeddings dans `.env`.
