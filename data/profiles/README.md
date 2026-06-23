# Profils d'entreprises simulés (validation — étape 3)

Les profils de référence sont définis **en code** dans
`maturai.validation.profiles.STANDARD_PROFILES` (cohérents et volontairement
incohérents), pour rester versionnés avec la logique de génération.

Ce dossier accueille les **profils exportés** (JSON) générés pour des campagnes
de validation reproductibles ou des jeux de test figés, par exemple :

```python
import json
from maturai.referential import get_default_referential
from maturai.validation import STANDARD_PROFILES, make_assessment

ref = get_default_referential()
for spec in STANDARD_PROFILES:
    a = make_assessment(spec, ref)
    # json.dump(a.model_dump(), open(f"data/profiles/{spec.name}.json", "w"), ...)
```
