"""Guarda el contrato real que genera FastAPI en docs/api/openapi.json (requiere fastapi)."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.api.app import crear_app  # noqa: E402
from src.infrastructure.composicion import crear_contenedor  # noqa: E402

if __name__ == "__main__":
    contrato = crear_app(crear_contenedor()).openapi()
    ruta = RAIZ / "docs" / "api" / "openapi.json"
    ruta.write_text(json.dumps(contrato, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Contrato guardado en {ruta}")
