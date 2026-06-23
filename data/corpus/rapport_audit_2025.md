# Rapport d'audit IA interne — ACME Corp (2025)

## Synthèse
L'audit constate une gouvernance IA en **construction** : la charte est publiée
mais certains dispositifs restent partiels.

## Constats par domaine

### Registre des risques IA
Un **registre des risques IA** existe sous forme de tableur, recensant une
dizaine de risques. Sa mise à jour est **irrégulière** (dernière révision il y a
plus de six mois). Maturité estimée : partielle.

### Conformité EU AI Act
L'équipe conformité **connaît le cadre de l'EU AI Act** mais **aucune
classification formelle** des systèmes par niveau de risque n'a été réalisée à
ce jour. Un inventaire partiel des systèmes IA en production existe (3 systèmes
sur ~8 recensés).

### Sécurité des LLM
Les **risques liés aux LLM** (prompt injection, fuite de données via les prompts)
sont identifiés dans une note interne, sans évaluation systématique. Aucune
politique formelle de **Shadow AI** n'est appliquée ; des usages de ChatGPT grand
public sont observés sans encadrement.

### Plan de réponse aux incidents IA
Aucun **plan de réponse aux incidents** spécifique à l'IA n'est documenté.

## Recommandations prioritaires
1. Formaliser la classification **EU AI Act** de l'ensemble des systèmes.
2. Industrialiser le **registre des risques IA** (mise à jour mensuelle).
3. Définir une politique de contrôle du **Shadow AI**.
