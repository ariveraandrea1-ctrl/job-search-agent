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
Radar: correos (POST /radar/email) — lee un correo de alertas (LinkedIn,
Workana...), saca las vacantes con app/parsers.py y las guarda sin duplicados.
Radar: oportunidades (POST /opportunities) — guarda una vacante o proyecto
freelance sin duplicados (huella = link normalizado o fuente:id).
Semana 7: perfil vigente (GET /profiles/{telegram_user_id}/current) — junta
el último perfil del CV con las respuestas de la entrevista (preferencias).
"""
import io
import json
import unicodedata
import uuid
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader
from docx import Document as DocxDocument
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document, InterviewAnswer, Opportunity, Profile
from app.parsers import elegir_lector, identificar_url, leer_mensaje_vacante, parse_getonbrd

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
    # Tema de la pregunta (ej. "salario"). Opcional para no romper llamadas viejas.
    topic: str | None = None


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
        topic=payload.topic,
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


# Nombres bonitos de cada tema, para mostrarlos en Telegram.
ETIQUETAS_TEMAS = {
    "rol_buscado": "Rol buscado",
    "modalidad": "Modalidad",
    "ciudad": "Ciudad",
    "salario": "Aspiración salarial",
    "disponibilidad": "Disponibilidad",
    "ingles": "Inglés",
    "contrato": "Tipo de contrato",
    "certificaciones": "Certificaciones",
}


def _perfil_vigente(db: Session, telegram_user_id: int):
    """Busca el último perfil del usuario y le junta las preferencias.

    Devuelve (perfil, preferencias, faltantes_sin_responder), o None si el
    usuario todavía no tiene ningún perfil.
    """
    perfil = db.scalars(
        select(Profile)
        .where(Profile.telegram_user_id == telegram_user_id)
        .order_by(Profile.created_at.desc())
        .limit(1)
    ).first()
    if perfil is None:
        return None

    respuestas = db.scalars(
        select(InterviewAnswer)
        .where(
            InterviewAnswer.telegram_user_id == telegram_user_id,
            InterviewAnswer.topic.is_not(None),
        )
        .order_by(InterviewAnswer.created_at.asc())
    ).all()
    # De la más vieja a la más nueva: la última respuesta de cada tema gana.
    preferencias: dict[str, str] = {}
    for respuesta in respuestas:
        preferencias[respuesta.topic] = respuesta.answer

    faltantes = perfil.data.get("faltantes", []) or []
    sin_responder = [tema for tema in faltantes if tema not in preferencias]
    return perfil, preferencias, sin_responder


@app.get("/profiles/{telegram_user_id}/current")
def get_current_profile(telegram_user_id: int, db: Session = Depends(get_db)) -> dict:
    """Devuelve el perfil vigente del usuario: CV + preferencias.

    - "perfil": el JSON del último perfil que armó la IA a partir del CV.
    - "preferencias": la respuesta MÁS RECIENTE de la entrevista para cada
      tema (salario, modalidad, ciudad...). Solo cuenta respuestas con tema.
    - "faltantes_sin_responder": temas que la IA marcó como faltantes y que
      todavía no tienen respuesta.
    Si el usuario no tiene ningún perfil, responde 404.
    """
    resultado = _perfil_vigente(db, telegram_user_id)
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="Este usuario todavía no tiene perfil. Primero debe enviar su CV.",
        )
    perfil, preferencias, sin_responder = resultado

    return {
        "profile_id": str(perfil.id),
        "prompt_version": perfil.prompt_version,
        "created_at": perfil.created_at.isoformat(),
        "perfil": perfil.data,
        "preferencias": preferencias,
        "faltantes_sin_responder": sin_responder,
    }


def _lista(valores, maximo: int = 8) -> str:
    """Une una lista en texto ("a, b, c"), cortando si es muy larga."""
    valores = [str(v) for v in (valores or []) if v]
    if not valores:
        return "—"
    texto = ", ".join(valores[:maximo])
    if len(valores) > maximo:
        texto += f" (+{len(valores) - maximo} más)"
    return texto


@app.get("/profiles/{telegram_user_id}/summary")
def get_profile_summary(telegram_user_id: int, db: Session = Depends(get_db)) -> dict:
    """Devuelve el perfil vigente como TEXTO listo para enviar por Telegram.

    Siempre responde 200 con {"text": ...}: si el usuario no tiene perfil,
    el texto le pide que envíe su CV (así n8n no tiene que manejar errores).
    Texto plano, sin Markdown, para que ningún carácter del CV rompa el envío.
    """
    resultado = _perfil_vigente(db, telegram_user_id)
    if resultado is None:
        return {
            "has_profile": False,
            "text": "Todavía no tengo tu perfil 📄 Envíame tu CV en PDF o Word y lo armo.",
        }
    perfil, preferencias, sin_responder = resultado
    datos = perfil.data
    contacto = datos.get("contacto") or {}
    habilidades = datos.get("habilidades") or {}

    lineas = ["👤 TU PERFIL", ""]
    lineas.append(f"Nombre: {contacto.get('nombre') or '—'}")
    lineas.append(f"Cargos: {_lista((datos.get('perfil') or {}).get('cargos'))}")
    ubicacion = ", ".join(x for x in [contacto.get("ciudad"), contacto.get("pais")] if x)
    lineas.append(f"Ubicación (CV): {ubicacion or '—'}")

    lineas += ["", "💼 EXPERIENCIA"]
    for empleo in datos.get("experiencia") or []:
        fechas = f"{empleo.get('inicio') or '?'} – {empleo.get('fin') or '?'}"
        lineas.append(f"• {empleo.get('cargo') or '—'} en {empleo.get('empresa') or '—'} ({fechas})")
    if not datos.get("experiencia"):
        lineas.append("—")

    lineas += ["", "🧪 PROYECTOS"]
    lineas.append(_lista([p.get("nombre") for p in datos.get("proyectos") or []]))

    lineas += ["", "🛠 HABILIDADES"]
    lineas.append(f"QA: {_lista(habilidades.get('qa'))}")
    lineas.append(f"Automatización: {_lista(habilidades.get('automatizacion'))}")
    lineas.append(f"Bases de datos: {_lista(habilidades.get('bases_de_datos'))}")
    lineas.append(f"Herramientas: {_lista(habilidades.get('herramientas'))}")

    idiomas = [
        f"{i.get('idioma')} ({i.get('nivel')})" if i.get("nivel") else i.get("idioma")
        for i in datos.get("idiomas") or []
        if i.get("idioma")
    ]
    lineas.append(f"Idiomas: {_lista(idiomas)}")

    lineas += ["", "🎯 PREFERENCIAS"]
    if preferencias:
        for tema, etiqueta in ETIQUETAS_TEMAS.items():
            if tema in preferencias:
                lineas.append(f"{etiqueta}: {preferencias[tema]}")
    else:
        lineas.append("—")

    if sin_responder:
        pendientes = [ETIQUETAS_TEMAS.get(t, t) for t in sin_responder]
        lineas += ["", f"⏳ Me falta saber: {_lista(pendientes)}"]

    lineas += [
        "",
        "✏️ Para corregir un dato escribe /corregir y el tema. Ejemplo: /corregir salario",
        "Temas: rol, modalidad, ciudad, salario, disponibilidad, ingles, contrato, certificaciones",
    ]

    texto = "\n".join(lineas)
    # Telegram acepta máximo 4096 caracteres por mensaje.
    if len(texto) > 4000:
        texto = texto[:3990] + "\n…"
    return {"has_profile": True, "text": texto}


def _normalizar_url(url: str) -> str:
    """Deja el link "limpio" para comparar vacantes.

    Quita los parámetros de seguimiento (?utm=..., &trk=...), el #ancla, la
    barra final y pasa el dominio a minúsculas. Así el mismo aviso que llega
    con links distintos (uno por cada correo de alerta) da la misma huella.
    """
    partes = urlsplit(url.strip())
    ruta = partes.path.rstrip("/")
    return urlunsplit((partes.scheme.lower(), partes.netloc.lower(), ruta, "", ""))


class OpportunityIn(BaseModel):
    """Lo que n8n manda por cada vacante encontrada por el radar."""

    telegram_user_id: int
    tipo: Literal["empleo", "freelance"]
    source: str
    title: str
    url: str
    external_id: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    raw: dict | None = None


def _guardar_oportunidad(db: Session, telegram_user_id: int, datos: dict):
    """Guarda una oportunidad SIN duplicados. Devuelve (creada, oportunidad).

    La huella (dedup_key) es "fuente:id" si la fuente trae un id propio, o el
    link normalizado si no. Si ya existe una con la misma huella para este
    usuario, no se guarda otra vez (creada = False).
    """
    source = datos["source"].strip().lower()
    if datos.get("external_id"):
        huella = f"{source}:{str(datos['external_id']).strip()}"
    else:
        huella = _normalizar_url(datos["url"])

    def buscar():
        return db.scalars(
            select(Opportunity).where(
                Opportunity.telegram_user_id == telegram_user_id,
                Opportunity.dedup_key == huella,
            )
        ).first()

    existente = buscar()
    if existente is not None:
        return False, existente

    oportunidad = Opportunity(
        telegram_user_id=telegram_user_id,
        tipo=datos["tipo"],
        source=source,
        external_id=datos.get("external_id"),
        title=datos["title"].strip(),
        company=datos.get("company"),
        location=datos.get("location"),
        url=datos["url"].strip(),
        description=datos.get("description"),
        raw=datos.get("raw"),
        dedup_key=huella,
    )
    db.add(oportunidad)
    try:
        db.commit()
    except IntegrityError:
        # Dos pedidos iguales llegaron casi al mismo tiempo: el otro ganó.
        db.rollback()
        return False, buscar()
    db.refresh(oportunidad)
    return True, oportunidad


@app.post("/opportunities")
def save_opportunity(payload: OpportunityIn, db: Session = Depends(get_db)) -> dict:
    """Guarda una oportunidad del radar, SIN duplicados.

    Responde created = false (y el id de la que ya estaba) si ya existía, así
    n8n puede reintentar sin miedo.
    """
    creada, oportunidad = _guardar_oportunidad(
        db, payload.telegram_user_id, payload.model_dump()
    )
    return {"created": creada, "id": str(oportunidad.id), "dedup_key": oportunidad.dedup_key}


def _guardar_lote(db: Session, telegram_user_id: int, ofertas: list[dict]):
    """Guarda varias oportunidades sin duplicados. Devuelve (nuevas, duplicadas)."""
    nuevas = []
    duplicadas = 0
    for oferta in ofertas:
        creada, oportunidad = _guardar_oportunidad(db, telegram_user_id, oferta)
        if creada:
            nuevas.append(
                {
                    "id": str(oportunidad.id),
                    "tipo": oportunidad.tipo,
                    "title": oportunidad.title,
                    "company": oportunidad.company,
                    "location": oportunidad.location,
                    "url": oportunidad.url,
                }
            )
        else:
            duplicadas += 1
    return nuevas, duplicadas


class RadarEmailIn(BaseModel):
    """Lo que n8n manda por cada correo que llega a la etiqueta Radar."""

    telegram_user_id: int
    from_address: str
    subject: str | None = None
    text: str | None = None


@app.post("/radar/email")
def radar_email(payload: RadarEmailIn, db: Session = Depends(get_db)) -> dict:
    """Lee un correo de alertas, saca sus vacantes y guarda las nuevas.

    Elige el lector según el remitente (app/parsers.py). Responde cuántas
    vacantes encontró, cuántas eran nuevas y cuántas ya estaban, más la lista
    de las NUEVAS (para que n8n avise por Telegram solo de esas).
    Si el remitente no tiene lector, responde parser = null y no guarda nada.
    """
    fuente, lector = elegir_lector(payload.from_address)
    if lector is None:
        return {"source": None, "parser": None, "found": 0, "created": 0,
                "duplicates": 0, "new_items": []}

    ofertas = lector(payload.text or "")
    for oferta in ofertas:
        oferta["raw"] = {"email_subject": payload.subject}
    nuevas, duplicadas = _guardar_lote(db, payload.telegram_user_id, ofertas)

    return {
        "source": fuente,
        "parser": lector.__name__,
        "found": len(ofertas),
        "created": len(nuevas),
        "duplicates": duplicadas,
        "new_items": nuevas,
        "telegram_text": _texto_telegram_radar(fuente, nuevas),
    }


NOMBRES_FUENTES = {
    "linkedin": "LinkedIn",
    "workana": "Workana",
    "computrabajo": "Computrabajo",
    "indeed": "Indeed",
    "greenhouse": "Greenhouse",
    "lever": "Lever",
    "manual": "otro sitio",
    "getonbrd": "Get on Board",
}


class RadarGetonbrdIn(BaseModel):
    """Lo que n8n manda: la respuesta COMPLETA de la API de Get on Board."""

    telegram_user_id: int
    response: dict


@app.post("/radar/getonbrd")
def radar_getonbrd(payload: RadarGetonbrdIn, db: Session = Depends(get_db)) -> dict:
    """Guarda las vacantes nuevas de Get on Board (API pública, sin scraping).

    Aplica un pre-filtro básico (remota o Colombia, hasta Semi Senior) y
    guarda sin duplicados. Misma respuesta que /radar/email + "skipped"
    (cuántas descartó el pre-filtro).
    """
    ofertas, descartadas = parse_getonbrd(payload.response)
    nuevas, duplicadas = _guardar_lote(db, payload.telegram_user_id, ofertas)
    return {
        "source": "getonbrd",
        "found": len(ofertas) + descartadas,
        "skipped": descartadas,
        "created": len(nuevas),
        "duplicates": duplicadas,
        "new_items": nuevas,
        "telegram_text": _texto_telegram_radar("getonbrd", nuevas),
    }

AYUDA_VACANTE = (
    "Para guardar una vacante, mándame:\n"
    "/vacante <link>\n"
    "o con un título para reconocerla:\n"
    "/vacante <link> QA Jr en Empresa X"
)


class RadarUrlIn(BaseModel):
    """Lo que n8n manda cuando escribes /vacante <link> en Telegram."""

    telegram_user_id: int
    text: str


@app.post("/radar/url")
def radar_url(payload: RadarUrlIn, db: Session = Depends(get_db)) -> dict:
    """Guarda una vacante que el usuario mandó a mano (link), SIN duplicados.

    No abre el link (nada de scraping): reconoce el portal y el id por el
    texto del link. Si la misma vacante ya había llegado por una alerta de
    correo, la reconoce (misma huella) y no la duplica. Siempre responde
    200 con telegram_text listo para mandar.
    """
    link, titulo = leer_mensaje_vacante(payload.text)
    if link is None:
        return {"ok": False, "created": False, "telegram_text":
                "No encontré ningún link en tu mensaje.\n\n" + AYUDA_VACANTE}

    datos = identificar_url(link)
    nombre = NOMBRES_FUENTES.get(datos["source"], datos["source"])
    datos["title"] = titulo or f"Vacante de {nombre} (sin título)"
    datos["raw"] = {"origen": "telegram", "mensaje": payload.text}
    creada, oportunidad = _guardar_oportunidad(db, payload.telegram_user_id, datos)

    if creada:
        texto = (f"✅ Guardé la vacante ({nombre}).\n"
                 f"• {oportunidad.title}\n   {oportunidad.url}")
        if not titulo:
            texto += "\n\nTip: puedes agregar un título después del link."
    else:
        texto = (f"👌 Esa vacante ya la tenías guardada ({nombre}).\n"
                 f"• {oportunidad.title}\n   {oportunidad.url}")
    return {
        "ok": True,
        "created": creada,
        "id": str(oportunidad.id),
        "source": datos["source"],
        "title": oportunidad.title,
        "url": oportunidad.url,
        "telegram_text": texto,
    }


def _texto_telegram_radar(fuente: str, nuevas: list[dict], maximo: int = 10) -> str | None:
    """Arma el aviso de Telegram con las oportunidades NUEVAS de un correo.

    Devuelve None si no hay nuevas (así n8n no manda nada). Texto plano, sin
    Markdown. Las freelance van primero y marcadas con ⚡ porque en freelance
    gana quien propone primero.
    """
    if not nuevas:
        return None
    nombre = NOMBRES_FUENTES.get(fuente, fuente)
    ordenadas = sorted(nuevas, key=lambda o: o["tipo"] != "freelance")
    freelance = sum(1 for o in nuevas if o["tipo"] == "freelance")

    if freelance == len(nuevas):
        titulo = f"⚡ {len(nuevas)} proyecto(s) freelance nuevo(s) en {nombre}"
    else:
        titulo = f"📥 {len(nuevas)} oportunidad(es) nueva(s) de {nombre}"
    lineas = [titulo, ""]

    for o in ordenadas[:maximo]:
        marca = "⚡ " if o["tipo"] == "freelance" else "• "
        detalle = " — ".join(x for x in [o.get("company"), o.get("location")] if x)
        lineas.append(f"{marca}{o['title']}" + (f" ({detalle})" if detalle else ""))
        lineas.append(f"   {o['url']}")
    if len(nuevas) > maximo:
        lineas.append(f"… y {len(nuevas) - maximo} más.")

    texto = "\n".join(lineas)
    return texto[:3990] + "\n…" if len(texto) > 4000 else texto
