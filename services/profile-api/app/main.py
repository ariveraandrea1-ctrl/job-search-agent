"""profile-api — servicio de dominio del Proyecto 1 (perfil, extracción, versiones).

Por ahora expone solo un endpoint de salud (/health) como parte del
andamiaje de la Semana 1. La lógica de dominio (perfiles, evidencia,
entrevista) se añade en incrementos posteriores.
"""
from fastapi import FastAPI

app = FastAPI(title="profile-api", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Health check usado por el healthcheck de docker-compose."""
    return {"status": "ok", "service": "profile-api"}
