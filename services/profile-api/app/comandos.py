"""Comandos del radar en Telegram (Semana 6). Funciones PURAS para pytest.

/mejores, /nuevas, /guardadas, /detalle N, /guardar N, /descartar N.
"N" es el número corto de la vacante (#12), que aparece en las listas.
"""
import re
from datetime import datetime, timezone

COMANDOS = ("mejores", "nuevas", "guardadas", "detalle", "guardar", "descartar")
CON_NUMERO = ("detalle", "guardar", "descartar")

AYUDA = (
    "Comandos del radar:\n"
    "/mejores — las vacantes con mejor puntaje\n"
    "/nuevas — las que llegaron hace poco\n"
    "/guardadas — las que guardaste\n"
    "/detalle 12 — todo sobre la vacante #12\n"
    "/guardar 12 — guardar la #12\n"
    "/descartar 12 — descartar la #12"
)

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
        lineas += ["", "Puntaje: todavía no la ha revisado la IA (se puntúan 5 por hora)."]
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
