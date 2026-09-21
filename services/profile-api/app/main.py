"""profile-api — servicio de dominio del Proyecto 1 (perfil, extracción, versiones).

Semana 1: endpoint de salud (/health).
Semana 3: endpoint de extracción de texto (/extract-text) — recibe un
archivo (PDF o DOCX) y devuelve el texto plano que contiene, para que
n8n pueda seguir procesándolo (guardarlo, analizarlo, etc.).
"""
import io

from fastapi import FastAPI, HTTPException, UploadFile
from pypdf import PdfReader
from docx import Document

app = FastAPI(title="profile-api", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Health check usado por el healthcheck de docker-compose."""
    return {"status": "ok", "service": "profile-api"}


def _extraer_texto_pdf(contenido: bytes) -> str:
    """Lee un PDF en memoria y devuelve el texto de todas sus páginas."""
    lector = PdfReader(io.BytesIO(contenido))
    paginas = [pagina.extract_text() or "" for pagina in lector.pages]
    return "\n".join(paginas).strip()


def _extraer_texto_docx(contenido: bytes) -> str:
    """Lee un DOCX en memoria y devuelve el texto de todos sus párrafos."""
    documento = Document(io.BytesIO(contenido))
    parrafos = [parrafo.text for parrafo in documento.paragraphs]
    return "\n".join(parrafos).strip()


@app.post("/extract-text")
async def extract_text(file: UploadFile) -> dict:
    """Recibe un archivo (PDF o DOCX) y devuelve su texto plano.

    n8n manda el archivo como 'multipart/form-data' con el campo
    llamado 'file'. Respondemos con JSON: nombre del archivo, cuántos
    caracteres tiene el texto extraído, y el texto en sí.
    """
    nombre = file.filename or ""
    contenido = await file.read()

    if nombre.lower().endswith(".pdf"):
        texto = _extraer_texto_pdf(contenido)
    elif nombre.lower().endswith(".docx"):
        texto = _extraer_texto_docx(contenido)
    else:
        raise HTTPException(
            status_code=400,
            detail="Formato no soportado. Solo se aceptan archivos .pdf o .docx.",
        )

    return {
        "filename": nombre,
        "char_count": len(texto),
        "text": texto,
    }
