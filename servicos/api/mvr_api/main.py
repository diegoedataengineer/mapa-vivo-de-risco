"""API do Mapa Vivo de Risco. Por enquanto: saúde e contrato das rotas (spec 03)."""

from __future__ import annotations

import os

from fastapi import FastAPI

app = FastAPI(title="Mapa Vivo de Risco", version="0.1.0")


@app.get("/saude")
def saude() -> dict:
    """Sinal de vida usado pelo health check do contêiner e pelo monitoramento."""
    return {"ok": True, "versao": app.version, "ambiente": os.environ.get("MVR_AMBIENTE", "local")}
