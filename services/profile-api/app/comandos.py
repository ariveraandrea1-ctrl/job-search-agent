"""Comandos del radar en Telegram (Semana 6). Funciones PURAS para pytest.

/mejores, /nuevas, /guardadas, /detalle N, /guardar N, /descartar N,
/buscar TEXTO, /resumen, /subir_cv, /pausar, /reanudar.
"N" es el número corto de la vacante (#12), que aparece en las listas.
"""
import re
from datetime import datetime, timezone

from app.busqueda import normalizar

COMANDOS = ("mejores", "nuevas", "guardadas", "detalle", "guardar", "descartar", "pausar", "reanudar",
            "buscar", "resumen", "subir_cv")
CON_NUMERO = ("detalle", "guardar", "descartar")

AYUDA = (
    "Comandos:\n"
    "/perfil — ver tu perfil\n"
    "/subir_cv — cómo enviarme tu hoja de vida\n"
    "/completar_perfil — responder las preguntas que faltan de tu perfil\n"
    "/buscar automation — buscar entre tus vacantes por palabra\n"
    "/resumen — el resumen de las últimas 24 horas\n"
    "/mejores — las vacantes con mejor puntaje\n"
    "/nuevas — las que llegaron hace poco\n"
    "/guardadas — las que guardaste\n"
    "/detalle 12 — todo sobre la vacante #12\n"
    "/guardar 12 — guardar la #12\n"
    "/descartar 12 — descartar la #12\n"
    "/preferencias — ver o cambiar las palabras de tu búsqueda\n"
    "/pausar — dejar de recibir vacantes por un tiempo\n"
    "/reanudar — volver a recibirlas"
)

TEXTOS_ESTADO_USUARIO = {
    "pausado": ("⏸ Listo, pausé tu radar: no te llegarán vacantes nuevas ni el resumen "
                "de la mañana. Cuando quieras volver, escribe /reanudar."),
    "activo": "▶️ ¡Bienvenida/o de vuelta! Tu radar está activo otra vez.",
}

NOMBRES_INGLES = {
    "no_requerido": "no requerido",
    "basico": "básico",
    "intermedio": "intermedio",
    "avanzado": "avanzado",
    "desconocido": "no lo dice",
}
NOMBRES_NIVEL = {
    "sin_experiencia": "sin experiencia",
    "junior": "junior",
    "semi_senior": "semi senior",
    "senior": "senior",
    "desconocido": "no lo dice",
}
NOMBRES_ESTADO = {"nueva": "nueva", "guardada": "guardada ⭐", "descartada": "descartada"}


def leer_comando(texto: str) -> tuple[str | None, int | None]:
    """De "/detalle 12" saca ("detalle", 12). Si no es un comando del radar: (None, None)."""
    m = re.match(r"^\s*/(\w+)(?:@\w+)?\s*#?\s*(\d+)?", texto or "")
    if not m or m.group(1).lower() not in COMANDOS:
        return None, None
    numero = int(m.group(2)) if m.group(2) else None
    return m.group(1).lower(), numero


TEXTO_SUBIR_CV = (
    "📄 Envíame tu hoja de vida como archivo, en PDF o Word (.docx), aquí mismo en el chat.\n\n"
    "La leo, armo tu perfil y te hago solo las preguntas que falten. "
    "Si ya me la habías enviado, la nueva reemplaza a la anterior (la vieja queda guardada como versión).\n"
    "Ojo: si el PDF es escaneado (una foto), no puedo leerlo; usa el PDF que exporta Word o Google Docs."
)

AYUDA_BUSCAR = ("🔎 Escribe /buscar y lo que buscas en el título o la empresa. Ejemplos:\n"
                "/buscar automation\n/buscar qa remoto\n/buscar bancolombia")


_MARKDOWN = re.compile(r"([_*`\[])")


def escapar_md(texto: str) -> str:
    """BUG-30: n8n manda los mensajes a Telegram con parse_mode Markdown (legacy).

    Un "_" suelto (ej. "/subir_cv" o "Bogotá_9740") abre una cursiva que no
    cierra y Telegram rechaza el mensaje ("can't parse entities"). Con "\\"
    delante, Telegram muestra el carácter normal.
    """
    return _MARKDOWN.sub(r"\\\1", texto)


def escapar_textos_telegram(datos):
    """Escapa todo campo "telegram_text" de una respuesta (también dentro de listas)."""
    if isinstance(datos, dict):
        return {k: (escapar_md(v) if k == "telegram_text" and isinstance(v, str)
                    else escapar_textos_telegram(v)) for k, v in datos.items()}
    if isinstance(datos, list):
        return [escapar_textos_telegram(x) for x in datos]
    return datos


def leer_busqueda(texto: str | None) -> str:
    """'/buscar QA Automation' → 'qa automation' (normalizado). Vacío si no escribió nada."""
    m = re.match(r"^\s*/buscar(?:@\w+)?\s*(.*)$", texto or "", re.IGNORECASE | re.DOTALL)
    return normalizar(m.group(1)) if m else ""


def coincide_busqueda(consulta: str, *campos: str | None) -> bool:
    """¿Todas las palabras de la consulta están en el título/empresa? (sin tildes, sin mayúsculas)."""
    palabras = normalizar(consulta).split()
    if not palabras:
        return False
    texto = normalizar(" ".join(c or "" for c in campos))
    return all(p in texto for p in palabras)


def _hace(segundos: float) -> str:
    dias = int(segundos // 86400)
    if dias >= 1:
        return f"hace {dias} día" + ("s" if dias > 1 else "")
    horas = int(segundos // 3600)
    if horas >= 1:
        return f"hace {horas} h"
    return "hace un momento"


def texto_antiguedad(v: dict, ahora: datetime | None = None) -> str:
    """'publicada hace 2 días' si la fuente da la fecha; si no, 'llegó hace 5 h'.

    published_at: segundos Unix (Get on Board). created_at: datetime de
    cuándo entró al radar.
    """
    ahora = ahora or datetime.now(timezone.utc)
    publicada = v.get("published_at")
    if isinstance(publicada, (int, float)):
        return "publicada " + _hace(ahora.timestamp() - publicada)
    llego = v.get("created_at")
    if isinstance(llego, datetime):
        if llego.tzinfo is None:
            llego = llego.replace(tzinfo=timezone.utc)
        return "llegó " + _hace((ahora - llego).total_seconds())
    return ""


def _linea_vacante(v: dict) -> str:
    puntos = f"{v['score']} pts" if v.get("score") is not None else "sin puntaje aún"
    detalle = " — ".join(x for x in [v.get("company"), v.get("location")] if x)
    linea = f"#{v['numero']} · {puntos} · {v['title']}"
    if detalle:
        linea += f" ({detalle})"
    edad = texto_antiguedad(v)
    if edad:
        linea += f" · {edad}"
    if v.get("url"):
        linea += f"\n   {v['url']}"
    return linea


def texto_lista(titulo: str, vacantes: list[dict], vacio: str) -> str:
    """Lista corta para Telegram: una línea por vacante + cómo ver el detalle."""
    if not vacantes:
        return vacio
    lineas = [titulo, ""] + [_linea_vacante(v) for v in vacantes]
    lineas += ["", "Escribe /detalle y el número para ver más (ej: /detalle "
               f"{vacantes[0]['numero']})."]
    return _recortar("\n".join(lineas))


def texto_detalle(v: dict) -> str:
    """Todo lo que sabemos de una vacante, incluido el análisis de la IA."""
    lineas = [f"#{v['numero']} · {v['title']}"]
    for etiqueta, clave in [("Empresa", "company"), ("Ubicación", "location"), ("Fuente", "source")]:
        if v.get(clave):
            lineas.append(f"{etiqueta}: {v[clave]}")
    edad = texto_antiguedad(v)
    if edad:
        lineas.append(edad[0].upper() + edad[1:])
    lineas.append(f"Estado: {NOMBRES_ESTADO.get(v.get('status'), v.get('status'))}")
    a = v.get("analysis") or {}
    if v.get("score") is None:
        lineas += ["", "Puntaje: todavía no la ha revisado la IA (las va puntuando cada hora)."]
    else:
        lineas += ["", f"Puntaje: {v['score']}/100"]
        if a.get("resumen"):
            lineas.append(a["resumen"])
        lineas.append(f"Inglés que piden: {NOMBRES_INGLES.get(a.get('ingles'), 'no lo dice')}")
        lineas.append(f"Nivel: {NOMBRES_NIVEL.get(a.get('nivel_vacante'), 'no lo dice')}")
        for titulo, clave, marca in [("A favor:", "razones_a_favor", "✅"),
                                     ("En contra:", "razones_en_contra", "➖"),
                                     ("⚠️ Señales de alerta:", "senales_alerta", "⚠️")]:
            if a.get(clave):
                lineas += ["", titulo] + [f"{marca} {r}" for r in a[clave]]
        if a.get("reglas_aplicadas"):
            lineas += ["", "Reglas aplicadas: " + "; ".join(a["reglas_aplicadas"])
                       + f" (la IA le había dado {a.get('puntaje_ia')})."]
    lineas += ["", v["url"], "", f"/guardar {v['numero']}   /descartar {v['numero']}"]
    return _recortar("\n".join(lineas))


def _recortar(texto: str) -> str:
    return texto[:3990] + "\n…" if len(texto) > 4000 else texto


def texto_resumen_diario(vacantes: list[dict], pendientes: int, horas: int = 24,
                         nombres_fuentes: dict | None = None, maximo: int = 5) -> str:
    """Resumen de lo que llegó en las últimas `horas` (para el mensaje de la mañana).

    vacantes: las que llegaron en ese periodo (sin descartadas).
    pendientes: cuántas de ellas todavía no tienen puntaje.
    """
    nombres_fuentes = nombres_fuentes or {}
    if not vacantes:
        return (f"☀️ Buenos días. En las últimas {horas} h no llegaron vacantes nuevas.\n"
                "Puedes revisar /mejores o /guardadas.")
    conteo: dict[str, int] = {}
    for v in vacantes:
        fuente = nombres_fuentes.get(v.get("source"), v.get("source"))
        conteo[fuente] = conteo.get(fuente, 0) + 1
    por_fuente = ", ".join(f"{f} {n}" for f, n in sorted(conteo.items(), key=lambda x: -x[1]))
    lineas = [f"☀️ Buenos días. Resumen del radar (últimas {horas} h):", "",
              f"Llegaron {len(vacantes)} vacante(s): {por_fuente}."]
    freelance = [v for v in vacantes if v.get("tipo") == "freelance"]
    if freelance:
        lineas.append(f"⚡ {len(freelance)} proyecto(s) freelance (responde rápido).")
    if pendientes:
        lineas.append(f"La IA aún no puntúa {pendientes} (las va puntuando cada hora).")

    con_alerta = [v for v in vacantes if (v.get("analysis") or {}).get("senales_alerta")]
    puntuadas = sorted((v for v in vacantes if v.get("score") is not None and v not in con_alerta),
                       key=lambda v: v["score"], reverse=True)
    if puntuadas:
        lineas += ["", "🏆 Las mejores de hoy:"] + [_linea_vacante(v) for v in puntuadas[:maximo]]
    if con_alerta:
        lineas += ["", "⚠️ Con señales de alerta (cuidado):"] + [
            f"#{v['numero']} · {v['title']}" for v in con_alerta[:maximo]]
    numero = (puntuadas or vacantes)[0]["numero"]
    lineas += ["", f"Escribe /detalle {numero} para ver más, o /nuevas para la lista completa."]
    return _recortar("\n".join(lineas))


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)


def email_valido(email: str | None) -> str | None:
    """Devuelve el correo limpio si tiene forma de correo; si no, None."""
    email = (email or "").strip().strip("<>").lower()
    return email if _EMAIL.match(email) else None


def texto_correo(texto_telegram: str) -> str:
    """El resumen de Telegram adaptado a correo (con cómo verlo en el bot)."""
    return (texto_telegram
            + "\n\n—\nEste resumen también te llegó por Telegram. "
              "Escríbele al bot /detalle y el número para ver una vacante, "
              "o /pausar para dejar de recibir resúmenes.")
