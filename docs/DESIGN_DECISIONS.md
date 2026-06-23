# Journal des décisions de conception & points ouverts

Ce document trace les décisions structurantes et les points à **valider/rectifier**
avec l'encadrant. Il évite que des choix implicites se figent sans débat.

## Décisions actées

| # | Décision | Justification |
|---|----------|---------------|
| D1 | **Python** comme langage du cœur scientifique | Écosystème scientifique mature (numpy/scipy, scikit-fuzzy, torch, neo4j, llama-index). Standard académique. |
| D2 | Échelle interne **[0,4]**, présentée **[1,5]** | Les modalités du questionnaire sont 0–4 (5 niveaux). Le 1–5 CMMI est obtenu par `+1` à l'affichage. Une seule conversion, localisée. |
| D3 | Incertitude portée par des **TFN** `(a,m,b)` | Forme à 2 paramètres interprétable, arithmétique en forme fermée, standard du Fuzzy AHP et des modèles de maturité flous. |
| D4 | Poids inter-axes par **centroïde des étendues synthétiques** (Fuzzy AHP), Chang conservé en comparatif | La méthode de Chang d'origine peut produire des poids **nuls** (limite connue) ; le centroïde normalisé est robuste tout en restant « fuzzy AHP ». |
| D5 | Règles d'incohérence = **écarts inter-axes** uniquement (un axe HAUT + un axe BAS) | Un profil uniformément bas est de la *faible maturité*, pas une *incohérence* ; il ne doit pas être doublement pénalisé. |
| D6 | Cœur du moteur flou **implémenté maison** (numpy), scikit-fuzzy en extra | Le calcul le plus testé ne doit pas dépendre d'une lib lourde ; contrôle total et exactitude vérifiable. scikit-fuzzy reste disponible comme implémentation Mamdani de référence pour la comparaison. |
| D7 | Graph-RAG, ANFIS, rapport LLM derrière des **interfaces** + mock/stub | Permet de développer et tester tout le pipeline sans Neo4j/torch/clé API. La bascule vers le réel ne touche aucun code aval. |
| D8 | Défuzzification = **centroïde** partout | Méthode unique de bout en bout → cohérence interne des scores. |

## Points ouverts — à valider / rectifier

### P1 — Données passe de 6 à 8 questions (couche IA-spécifique) ⚠️
Le récapitulatif initial donne **Données = 6 questions, 20 %**. Mais tes questions
**Q15bis** (représentativité / biais des données d'entraînement) et **Q18bis**
(traçabilité / lineage) sont la *couche IA-spécifique* de cet axe. Les intégrer
porte Données à **8 questions**.

**Décision prise** : on les intègre (c'est le cœur du double ancrage), on tague
chaque question `layer = generic | ai_specific`, et le **poids de l'axe reste
20 %** (les questions internes sont équipondérées par défaut).
**À confirmer** : (a) garder ces deux questions dans Données ; (b) conserver le
poids d'axe à 20 % malgré 8 questions ; (c) leur placement (Q15bis → 2.1 Qualité,
Q18bis → 2.3 Métadonnées).

### P2 — Poids des sous-domaines et des questions
Actuellement **équipondérés** (tous à 1.0, normalisés). Les poids *faisant foi*
ne sont calibrés par Fuzzy AHP qu'au **niveau des axes**.
**À décider** : faut-il aussi calibrer les sous-domaines par AHP (plus lourd à
éliciter), ou l'équipondération intra-axe suffit-elle pour le mémoire ?

### P3 — Hyperparamètres de fuzzification
`base_spread = 0.5`, `max_extra_spread = 1.0` (cf. `ScoringConfig`). Ces valeurs
gouvernent la largeur des TFN. Elles sont **plausibles mais à justifier** : soit
par sensibilité (protocole de validation), soit par calibration sur avis d'experts.

### P4 — Intensité de la pénalité d'incohérence
`incoherence_strength = 1.0` et univers de pénalité `[0, 1]` (en points de score).
**À calibrer** : quelle baisse maximale de score une incohérence majeure doit-elle
provoquer ? À discuter avec l'encadrant / valider sur profils experts.

### P5 — Multi-répondants
Le modèle `QuestionResponse` porte une `confidence` et une `source`, mais
l'agrégation **inter-répondants** (plusieurs parties prenantes répondant à la
même question, pondérées par leur légitimité via Q5/Q6) n'est pas encore
implémentée. À spécifier (moyenne floue pondérée par rôle ? consensus ?).

### P6 — Référentiels : versions exactes à citer
Les sources sont nommées (PwC, DAMA-DMBOK, ISO/IEC 42001, NIST AI RMF, EU AI Act,
McKinsey). Pour le mémoire, **figer les versions/années précises** et les pages
des clauses citées (cf. `docs/references.bib`).
