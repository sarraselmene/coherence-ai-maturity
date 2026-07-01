
#!/usr/bin/env bash
# Mise en place de l'environnement de développement (macOS / Linux).
# Usage :  bash scripts/setup.sh
set -euo pipefail

echo "== MaturAI : mise en place de l'environnement (macOS/Linux) =="

# 1. Python 3.11+
PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Python 3.11+ introuvable. Installer via : brew install python@3.12" >&2
  exit 1
fi
echo "Python détecté : $($PY --version)"

# 2. venv
if [ ! -d ".venv" ]; then
  echo "Création du venv .venv ..."
  "$PY" -m venv .venv
fi

# 3. Dépendances (cœur + dev + web)
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e ".[dev,web]"

echo ""
echo "Terminé. Activer :  source .venv/bin/activate"
echo "Tests       :  pytest -q"
echo "Interface   :  python scripts/run_web.py   (http://127.0.0.1:8000)"
echo "Extras IA   :  pip install -e \".[fuzzy,graphrag,report]\""
