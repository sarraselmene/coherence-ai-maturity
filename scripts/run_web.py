"""Lance l'interface web MaturAI (FastAPI + SPA).

Prérequis :
    pip install -e ".[web]"
Usage :
    python scripts/run_web.py            # http://127.0.0.1:8000
    python scripts/run_web.py 8080       # port personnalisé
"""

from __future__ import annotations

import sys


def main() -> None:
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"MaturAI — interface web sur http://127.0.0.1:{port}")
    uvicorn.run("maturai.web.app:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
