"""Lectores ("parsers") de correos de alertas de empleo.

Cada lector recibe el TEXTO plano de un correo y devuelve una lista de
oportunidades (diccionarios con tipo, source, title, company, location, url,
external_id y description). Son funciones puras: no tocan la base de datos,
así se pueden probar con pytest sin levantar nada.

Formatos soportados (vistos en correos reales, 2026-09-30):
- LinkedIn (jobalerts-noreply@ y jobs-noreply@): bloques
  "Título / Empresa / Ubicación / ... / Ver anuncio de empleo: URL".
- Workana (notification@notifications.workana.com): bloques
  "Título / ----- / descripción / Leer más: URL".
- Computrabajo (empleos_co@): los correos de "resumen" NO traen vacantes
  individuales (solo un conteo y un link a la lista), así que devuelven [].
- Indeed: pendiente (todavía no tenemos un correo de ejemplo).
"""
import re

# ---------------------------------------------------------------- LinkedIn

_LINKEDIN_VER = re.compile(
    r"(?:Ver anuncio de empleo|View job):\s*"
    r"(https://www\.linkedin\.com/\S*?/jobs/view/(\d+)\S*)"
)

# Líneas que NO son título/empresa/ubicación (encabezados y adornos).
_LINKEDIN_RUIDO = (
    "tu alerta de empleo",
    "your job alert",
    "nuevos empleos",
    "new jobs",
    "gestionar alertas",
    "manage alerts",
    "empleos de",
    "tus otros empleos",
    "el empleo guardado",
    "ver todos",
    "see all",
    "solicitar",
    "solicitud sencilla",
    "easy apply",
    "esta empresa busca",
    "promocionado",
    "promoted",
    "editar alerta",
    "edit alert",
)
_LINKEDIN_RUIDO_RE = re.compile(
    r"^\d+\s+(contactos?|connections?|exalumnos?|alumni|personas?|people"
    r"|candidatos?|solicitantes?|applicants?)\b",
    re.IGNORECASE,
)


def _es_ruido_linkedin(linea: str) -> bool:
    baja = linea.lower()
    if "http" in linea or "<" in linea or set(linea) <= set("-—– "):
        return True
    if _LINKEDIN_RUIDO_RE.match(linea):
        return True
    return any(baja.startswith(r) for r in _LINKEDIN_RUIDO)


def parse_linkedin(texto: str) -> list[dict]:
    """Saca las vacantes de un correo de alertas / empleos de LinkedIn."""
    resultados = []
    vistos = set()
    inicio_bloque = 0
    for m in _LINKEDIN_VER.finditer(texto):
        job_id = m.group(2)
        bloque = texto[inicio_bloque : m.start()]
        inicio_bloque = m.end()
        lineas = [l.strip() for l in bloque.splitlines()]
        lineas = [l for l in lineas if l and not _es_ruido_linkedin(l)]
        if len(lineas) < 2 or job_id in vistos:
            continue
        vistos.add(job_id)
        # Antes del primer empleo de cada sección hay encabezados (el texto de
        # la alerta, "Nuevos empleos de tus otras alertas"...). El empleo son
        # siempre las ÚLTIMAS líneas del bloque: título, empresa, ubicación.
        if len(lineas) >= 3:
            titulo, empresa, ubicacion = lineas[-3:]
        else:
            titulo, empresa, ubicacion = lineas[0], lineas[1], None
        resultados.append(
            {
                "tipo": "empleo",
                "source": "linkedin",
                "external_id": job_id,
                "title": titulo.lstrip("-–— ").strip(),
                "company": empresa,
                "location": ubicacion,
                "url": f"https://www.linkedin.com/jobs/view/{job_id}/",
                "description": None,
            }
        )
    return resultados


# ----------------------------------------------------------------- Workana

_WORKANA_PROYECTO = re.compile(
    r"^[ \t]*(?P<title>\S[^\n]*?)[ \t]*\n"
    r"[ \t]*-{5,}[ \t]*\n"
    r"(?P<desc>.*?)"
    r"Leer más:\s*(?P<url>https://www\.workana\.com/job/(?P<slug>[^\s?#]+)\S*)",
    re.MULTILINE | re.DOTALL,
)


def parse_workana(texto: str) -> list[dict]:
    """Saca los proyectos freelance de un correo de Workana."""
    resultados = []
    for m in _WORKANA_PROYECTO.finditer(texto):
        slug = m.group("slug").rstrip("/")
        descripcion = " ".join(m.group("desc").split()) or None
        resultados.append(
            {
                "tipo": "freelance",
                "source": "workana",
                "external_id": slug,
                "title": m.group("title").strip(),
                "company": None,
                "location": "Remoto",
                "url": f"https://www.workana.com/job/{slug}",
                "description": descripcion,
            }
        )
    return resultados


# ------------------------------------------------------------- Computrabajo


def parse_computrabajo(texto: str) -> list[dict]:
    """Los correos de resumen de Computrabajo no traen vacantes sueltas.

    Solo dicen "Tenemos N vacantes..." y un link a la lista, que no leemos
    automáticamente (scraping va contra sus condiciones). Devuelve [].
    """
    return []


# --------------------------------------------------------------- Despacho

LECTORES = {
    "linkedin.com": ("linkedin", parse_linkedin),
    "workana.com": ("workana", parse_workana),
    "computrabajo.com": ("computrabajo", parse_computrabajo),
}


def elegir_lector(remitente: str):
    """Según el correo del remitente, devuelve (fuente, función) o (None, None)."""
    remitente = (remitente or "").lower()
    for dominio, (fuente, funcion) in LECTORES.items():
        if remitente.endswith(dominio):
            return fuente, funcion
    return None, None
