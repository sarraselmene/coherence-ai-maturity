"""Chargement du référentiel : JSON → validation schéma → modèles → invariants.

Pipeline de chargement en trois temps, du plus syntaxique au plus sémantique :

1. lecture du JSON ;
2. validation **structurelle** contre le JSON Schema (jsonschema) ;
3. parsing en modèles pydantic puis validation **sémantique** métier.

Échouer à n'importe quelle étape lève une exception explicite : le référentiel
étant le socle de tout le système, on refuse de démarrer sur une base douteuse.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from maturai.config import REFERENTIAL_PATH, REFERENTIAL_SCHEMA_PATH
from maturai.domain.referential import Referential
from maturai.referential.validators import validate_referential


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _validate_schema(data: dict, schema_path: Path) -> None:
    """Validation structurelle via jsonschema (import paresseux et optionnel)."""
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - dépendance optionnelle
        # On n'empêche pas le chargement si jsonschema n'est pas installé ;
        # la validation pydantic + sémantique reste appliquée.
        return
    schema = _load_json(schema_path)
    jsonschema.validate(instance=data, schema=schema)


def load_referential(
    path: Path | str = REFERENTIAL_PATH,
    schema_path: Path | str = REFERENTIAL_SCHEMA_PATH,
    *,
    validate_schema: bool = True,
) -> Referential:
    """Charge, valide et renvoie le référentiel.

    Args:
        path: chemin du ``questions.json``.
        schema_path: chemin du JSON Schema.
        validate_schema: désactivable pour les tests unitaires sur des
            référentiels partiels.

    Raises:
        FileNotFoundError, json.JSONDecodeError, jsonschema.ValidationError,
        pydantic.ValidationError, ReferentialError.
    """
    path = Path(path)
    data = _load_json(path)

    if validate_schema:
        _validate_schema(data, Path(schema_path))

    ref = Referential.model_validate(data)
    validate_referential(ref)
    return ref


@lru_cache(maxsize=1)
def get_default_referential() -> Referential:
    """Référentiel par défaut, mis en cache (chargé une seule fois)."""
    return load_referential()
