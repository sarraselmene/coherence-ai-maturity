# Corpus de documents (Graph-RAG — étape 5)

Déposer ici les **documents fictifs cohérents** servant à l'extraction de preuves
Graph-RAG. Suggestions (alignées sur les `target_entities` du référentiel) :

- `charte_ia.pdf` — charte éthique IA (Q28), comité IA (Q30)
- `rapport_audit_2025.pdf` — registre de risques (Q29), classification EU AI Act (Q35)
- `organigramme.pdf` — équipe data/IA (Q19), AI Officer (Q30)
- `politique_donnees.pdf` — gouvernance des données (Q17), catalogue (Q18)
- `politique_cyber.pdf` — risques LLM (Q31), Shadow AI (Q32)
- `rapport_financier.pdf` — budget IA (Q11, Q42), CA (Q4)

Tant que le pipeline réel n'est pas branché, le `MockEvidenceExtractor`
(`maturai.graphrag.mock`) fournit des preuves de substitution cohérentes avec ces
documents.
