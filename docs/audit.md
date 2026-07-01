# Audit technique & feuille de route d'amélioration

> Audit du 2026-06-30. Méthode : revue multi-agents (9 dimensions lues sur le
> code réel) + synthèse priorisée + **critique adversariale qui a re-vérifié les
> findings dans les sources** (mypy relancé, code relu). 69 findings bruts →
> feuille de route ci-dessous. Document vivant : cocher au fur et à mesure.

Légende effort/impact : 🟢 faible · 🟡 moyen · 🔴 élevé.

---

## A. Corrections prioritaires (défauts confirmés — fort impact / faible effort)

Ces points ne sont pas des « améliorations » mais des défauts qu'un jury
repérerait. Tous vérifiés dans le code.

| #   | Défaut                                                                             | Fichiers                                                      | Impact | Effort | Statut |
| --- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------- | :----: | :----: | :----: |
| A1  | Intervalle de crédibilité encore inversable (forte pénalité + maturité basse)      | `scoring/engine.py`, `tests/test_engine.py`                   |   🔴   |   🟢   |   ☐    |
| A2  | `mypy` ne s'exécute pas (`python_version="3.11"` vs venv 3.12 + numpy 2.x)         | `pyproject.toml`                                              |   🔴   |   🟢   |   ☐    |
| A3  | API renvoie 500 au lieu de 422 sur entrée invalide                                 | `web/schemas.py`, `web/app.py`, `domain/responses.py`         |   🔴   |   🟢   |   ☐    |
| A4  | ROI absurde sur budget nul (`max(budget,1e-9)` → ~1e11)                            | `roi/monte_carlo.py`, `domain/responses.py`, `web/app.py`     |   🔴   |   🟢   |   ☐    |
| A5  | `TFN.membership` fausse aux épaules `(0,0,1)`/`(3,4,4)` (niveaux Initial/Optimisé) | `domain/fuzzy_number.py`, `scoring/membership.py`             |   🟡   |   🟢   |   ☐    |
| A6  | Valeur propre AHP par partie réelle au lieu du module max (Perron-Frobenius)       | `weighting/consistency.py`, `tests/test_fuzzy_ahp.py`         |   🟢   |   🟢   |   ☐    |
| A7  | `**req.context` non filtré (500 sur clé `sector`) + payloads non bornés (DoS)      | `web/schemas.py`, `web/app.py`, `domain/responses.py`         |   🔴   |   🟢   |   ☐    |
| A8  | QCM franchissable sans répondre → scoring silencieux partiel                       | `web/static/app.js`, `web/app.py`                             |   🔴   |   🟢   |   ☐    |
| A9  | Aucune persistance du formulaire (F5 = perte des 33 réponses)                      | `web/static/app.js`                                           |   🔴   |   🟢   |   ☐    |
| A10 | Secret `"change-me-please"` versionné + aucun `load_dotenv()`                      | `config.py`, `graphrag/neo4j_client.py`, `graphrag/ingest.py` |   🟡   |   🟢   |   ☐    |

**Détail des correctifs :**

- **A1** — après décalage de pénalité, clamper **les deux** bornes sur `[0,4]`,
  puis `lo, hi = sorted((lo, hi))` et garantir `lo ≤ global_crisp ≤ hi`.
  (Le correctif précédent ne clampait que `lo` par le bas → cas résiduel.)
- **A2** — `python_version = "3.12"` (ou supprimer), borner `numpy>=1.26,<3`,
  relancer `mypy src tests` jusqu'à « Success », citer la preuve dans le mémoire.
- **A3** — `answers` validé `Annotated[int, Field(ge=0, le=4)]`, `confidences`
  dans `[0,1]` ; `@app.exception_handler(ValueError) → HTTPException(422)`.
- **A4** — `Field(ge=0)` sur `ROIInputs` ; `ValueError` explicite si
  `ai_budget<=0` ou `hours_per_week<=0` ; déplacer la garde de `app.py` dans la lib.
- **A5** — déléguer `TFN.membership` à `trimf` ; tests `(0,0,1).membership(0)==1`.
- **A6** — `idx = argmax(np.abs(eigvals))` ; test sur matrice incohérente connue.
- **A7** — sous-modèle pydantic typé pour le contexte (region, headcount, …) ;
  bornes de cardinalité ; middleware rejetant un corps > ~256 Ko.
- **A8** — `navButtons('Suivant', answered===total)` + réactivation au clic ;
  côté API, 422 si nombre de réponses < attendu.
- **A9** — sérialiser `state` dans `localStorage` à chaque mutation ; au
  démarrage, proposer « Reprendre l'évaluation » ; vider après POST réussi.
- **A10** — lecture env via `field(default_factory=...)` + `load_dotenv()` aux
  points d'entrée ; `RuntimeError` claire si `NEO4J_PASSWORD` absent.

---

## B. Améliorations stratégiques (valeur scientifique pour le mémoire)

| #   | Amélioration                                                                                                                                | Fichiers                                                      | Impact | Effort |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | :----: | :----: |
| B1  | Tests de propriété `hypothesis` sur l'arithmétique floue (déjà installé, inutilisé)                                                         | `tests/test_fuzzy_*` , `pyproject.toml`                       |   🔴   |   🟡   |
| B2  | Lever la circularité de la distillation ANFIS (profils incohérents + test hors-distribution + clarifier « fidélité » vs « généralisation ») | `anfis/training.py`, `docs/methodology/03-anfis.md`           |   🔴   |   🟡   |
| B3  | Monotonie des centres MF (`cumsum(softplus)`) + early-stopping + L2                                                                         | `anfis/model.py`, `anfis/training.py`, `tests/test_anfis.py`  |   🔴   |   🟡   |
| B4  | Snapshots numériques (scores de référence gelés)                                                                                            | `tests/test_snapshots.py` (nouveau)                           |   🔴   |   🟢   |
| B5  | Comparaison à 3 colonnes testée (classique/Mamdani/ANFIS) dans `compare.py`                                                                 | `validation/compare.py`, `tests/test_anfis.py`                |   🟡   |   🟡   |
| B6  | Analyse de sensibilité ROI (**Spearman** / tornado, sur échantillons existants)                                                             | `roi/monte_carlo.py`                                          |   🔴   |   🟡   |
| B7  | Analyse de sensibilité scoring (`base_spread`, `incoherence_strength` — P3/P4)                                                              | `config.py`, `validation/campaign.py`                         |   🔴   |   🟡   |
| B8  | Test e2e Graph-RAG → réconciliation → score → ROI → rapport                                                                                 | `tests/test_e2e.py` (nouveau)                                 |   🔴   |   🟡   |
| B9  | Injection de prompt dans l'extraction Graph-RAG (menace + mitigation documentées)                                                           | `graphrag/extract.py`, `docs/DESIGN_DECISIONS.md`             |   🟡   |   🟡   |
| B10 | Agrégation multi-répondants (P5 : désaccord → confiance ↓ → TFN élargi)                                                                     | `domain/responses.py`, `docs/methodology/04-uncertainty.md`   |   🔴   |   🟡   |
| B11 | Tracer/sourcer les constantes ROI (47 sem, 1600 h, provisions)                                                                              | `roi/monte_carlo.py`, `docs/methodology/07-roi-montecarlo.md` |   🟡   |   🟢   |
| B12 | Sauvegarde/chargement du modèle ANFIS entraîné (checkpoint `.pt`)                                                                           | `anfis/model.py`, `scripts/run_anfis.py`                      |   🟡   |   🟢   |
| B13 | Accessibilité du QCM (role=radiogroup, navigation clavier, focus-visible, aria-live)                                                        | `web/static/app.js`, `web/static/styles.css`                  |   🔴   |   🟡   |
| B14 | Export PDF / impression du rapport (`window.print` + `@media print`)                                                                        | `web/static/app.js`, `web/static/styles.css`                  |   🟡   |   🟡   |

---

## C. Fil transversal « reproductibilité & intégrité » (ajouté par la critique)

Conditionne la **citabilité des chiffres** du mémoire — souvent sous-estimé.

- **C1 — Reproductibilité de bout en bout** : la graine ROI (`seed=42`) n'est ni
  passée par l'API ni renvoyée → un résultat affiché n'est pas rejouable. Tracer
  et retourner `seed` + `credibility_alpha` ; `torch.use_deterministic_algorithms`
  ; logger versions numpy/torch.
- **C2 — Valider le référentiel comme contrat testé** : poids qui somment à 1,
  exactement 5 modalités 0–4 par question, `target_entities` cohérentes. Un
  `questions.json` mal édité (transfert macOS→PC) fausse tout en silence.
- **C3 — Centraliser et tester la conversion d'échelle `[0,4] → 1–5`** (le `+1`
  est dispersé dans le JS et le rapport) → éviter un off-by-one dans les captures.
- **C4 — Invariant `lo ≤ score ≤ hi` garanti universellement** (property test),
  pas seulement sur un profil.
- **C5 — Mesure de latence/coût CPU** du `POST /api/assess` (scoring + 20 000
  tirages Monte Carlo, uvicorn mono-worker) : un simple chrono sur 10 requêtes
  séquentielles + `lru_cache` du payload référentiel suffit à objectiver.

---

## D. À NE PAS faire (sur-dimensionné pour un mémoire — gain nul en soutenance)

- ❌ CI multi-OS + couverture verrouillée → un `scripts/check.(ps1|sh)`
  reproductible (lint+format+mypy+pytest) suffit.
- ❌ Persistance SQLModel multi-tenant + historique + métriques d'usage → réflexe
  produit/SaaS. Au plus : `assessment_id` + horodatage + score sérialisé pour rejouer.
- ❌ Dockerfile pour l'app web (pas de Docker ; la démo se fait avec `uvicorn`).
- ❌ Rate limiting / CORS configurable / middleware anti-DoS → durcissement
  « Internet exposé » inutile en local même-origine.
- ❌ Refonte `app.js` en modules ES + Vitest → garder le vanilla zéro-dépendance ;
  juste un **test ciblé** de `mdToHtml`/échappement (risque XSS du rapport LLM).
- ❌ SALib / indices de Sobol pour le ROI → Spearman suffit (modèle à 3–4 entrées).

---

## Ordre d'exécution recommandé

1. **Lot A complet** (A1→A10) — corrections confirmées, faible effort, fort
   rendement crédibilité. Commencer par A1, A2, A3, A4 (les plus visibles).
2. **C2 + C3 + C4** — intégrité du référentiel et cohérence d'échelle (socle).
3. **B1, B4** — property tests + snapshots (verrouillent la correction numérique).
4. **B2, B3, B6, B7, B8** — volet scientifique du mémoire (ANFIS honnête,
   sensibilité, e2e).
5. **B9, B10, B11, B13, B14** — robustesse RAG, P5, accessibilité, export PDF.
6. **C1, C5** — reproductibilité tracée + mesure de latence.
7. Reléguer le **lot D** en « pistes d'industrialisation » de la conclusion.

> Points méthodologiques ouverts liés : voir [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)
> (P1 Données 6→8, P2 poids sous-domaines, P3/P4 hyperparamètres, P5 multi-répondants,
> P6 versions des référentiels).
