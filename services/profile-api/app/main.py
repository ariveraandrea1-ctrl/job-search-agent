"""profile-api — servicio de dominio del Proyecto 1 (perfil, extracción, versiones).

Semana 1: endpoint de salud (/health).
Semana 3: endpoint de extracción de texto (/extract-text) — recibe un
archivo (PDF o DOCX) y devuelve el texto plano que contiene, para que
n8n pueda seguir procesándolo (guardarlo, analizarlo, etc.).
Semana 4: endpoint de guardado (/documents) — recibe el texto ya
extraído y lo guarda en PostgreSQL, para que no se pierda.
Semana 5: endpoint de entrevista (/interview-answers) — recibe la
respuesta que el usuario da a la pregunta de entrevista (la que se
manda justo después de confirmar la recepción del CV) y la guarda en
PostgreSQL, igual que se hace con el texto del CV.
Semana 6: endpoint de perfil (/profiles) — recibe el JSON que la IA armó
a partir del CV, revisa que sea JSON válido y lo guarda en PostgreSQL.
"""
import io
import json
import unicodedata
import uuid

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader
from docx import Document as DocxDocument
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document, InterviewAnswer, Profile

app = FastAPI(title="profile-api", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Health check usado por el healthcheck de docker-compose."""
    return {"status": "ok", "service": "profile-api"}


def _extraer_texto_pdf(contenido: bytes) -> str:
    """Lee un PDF en memoria y devuelve el texto de todas sus páginas."""
    lector = PdfReader(io.BytesIO(contenido))
    paginas = [pagina.extract_text() or "" for pagina in lector.pages]
    texto = "\n".join(paginas).strip()
    # Algunos PDF guardan "fi", "fl", etc. como un solo caracter especial
    # (ligadura: "ﬁnal" en vez de "final"). NFKC los convierte en letras
    # normales para que la IA y las busquedas vean el texto correcto.
    return unicodedata.normalize("NFKC", texto)


def _extraer_texto_docx(contenido: bytes) -> str:
    """Lee un DOCX en memoria y devuelve el texto de todos sus párrafos."""
    documento = DocxDocument(io.BytesIO(contenido))
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


class DocumentIn(BaseModel):
    """Lo que n8n manda para guardar un CV ya extraído."""

    telegram_user_id: int
    filename: str
    char_count: int
    text: str


@app.post("/documents")
def save_document(payload: DocumentIn, db: Session = Depends(get_db)) -> dict:
    """Guarda en PostgreSQL el texto de un CV ya extraído.

    n8n llama esto después de /extract-text, mandando el resultado de
    ese paso más el chat_id de Telegram del usuario. Así el texto
    queda guardado de forma permanente, en vez de perderse.
    """
    documento = Document(
        telegram_user_id=payload.telegram_user_id,
        filename=payload.filename,
        char_count=payload.char_count,
        extracted_text=payload.text,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)

    return {
        "id": str(documento.id),
        "created_at": documento.created_at.isoformat(),
    }


class InterviewAnswerIn(BaseModel):
    """Lo que n8n manda cuando el usuario contesta la pregunta de entrevista."""

    telegram_user_id: int
    question: str
    answer: str


@app.post("/interview-answers")
def save_interview_answer(
    payload: InterviewAnswerIn, db: Session = Depends(get_db)
) -> dict:
    """Guarda en PostgreSQL la respuesta del usuario a la pregunta de entrevista.

    n8n llama esto después de que el usuario responde (por Telegram) a la
    pregunta que se le hizo justo después de confirmar la recepción del
    CV. Así la respuesta queda guardada de forma permanente, en vez de
    perderse, igual que ya pasa con el texto extraído del CV.
    """
    respuesta = InterviewAnswer(
        telegram_user_id=payload.telegram_user_id,
        question=payload.question,
        answer=payload.answer,
    )
    db.add(respuesta)
    db.commit()
    db.refresh(respuesta)

    return {
        "id": str(respuesta.id),
        "created_at": respuesta.created_at.isoformat(),
    }


class ProfileIn(BaseModel):
    """Lo que n8n manda después de "Analizar CV con IA".

    "text" es el JSON del perfil tal como lo devuelve ai-model-router
    (viene como texto, no como objeto). "document_id" es el id que
    devolvió /documents al guardar el CV (opcional).
    """

    telegram_user_id: int
    document_id: uuid.UUID | None = None
    text: str
    provider: str
    prompt_version: str


@app.post("/profiles")
def save_profile(payload: ProfileIn, db: Session = Depends(get_db)) -> dict:
    """Guarda en PostgreSQL el perfil que la IA armó a partir del CV.

    Antes de guardar revisa que "text" sea un JSON válido con forma de
    objeto ({...}). Si la IA devolvió algo roto, responde 422 con un
    mensaje claro y NO guarda nada, para no llenar la tabla de basura.
    """
    try:
        datos = json.loads(payload.text)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=422,
            detail=f"La IA no devolvió un JSON válido: {error.msg} (posición {error.pos}).",
        )
    if not isinstance(datos, dict):
        raise HTTPException(
            status_code=422,
            detail="La IA devolvió JSON, pero no es un objeto {...} con el perfil.",
        )

    perfil = Profile(
        telegram_user_id=payload.telegram_user_id,
        document_id=payload.document_id,
        data=datos,
        provider=payload.provider,
        prompt_version=payload.prompt_version,
    )
    db.add(perfil)
    db.commit()
    db.refresh(perfil)

    return {
        "id": str(perfil.id),
        "created_at": perfil.created_at.isoformat(),
        "faltantes": datos.get("faltantes", []),
    }
