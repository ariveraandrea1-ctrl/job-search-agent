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
- Indeed (donotreply@jobalert.indeed.com): bloques separados por línea en
  blanco "Título / Empresa - Ubicación / (salario, etiquetas) / descripción /
  fecha / URL con jk=<id>".
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


# ------------------------------------------------------------------ Indeed

_INDEED_URL = re.compile(
    r"https://(?:[a-z]{2,3}\.)?indeed\.com/\S*?[?&]jk=([0-9a-f]+)\S*", re.IGNORECASE
)
# Líneas "de adorno" dentro de un bloque de Indeed que no son la descripción.
_INDEED_ETIQUETAS = (
    "postulación vía indeed",
    "postularse fácilmente",
    "easily apply",
    "esta empresa responde",
    "responsive employer",
    "recién publicado",
    "just posted",
    "hace ",
    "urgente",
)
# Línea de salario: empieza con "$" (o "Desde $" / "Hasta $"). Una descripción
# que MENCIONA un salario en medio de la frase sí se conserva.
_INDEED_SALARIO = re.compile(r"^(?:desde |hasta |de |from |up to )?\$", re.IGNORECASE)
_INDEED_REMOTO = {"desde casa", "remoto", "remote", "trabajo remoto"}


def parse_indeed(texto: str) -> list[dict]:
    """Saca las vacantes de un correo de alertas de Indeed."""
    resultados = []
    vistos = set()
    for bloque in re.split(r"\n[ \t]*\n", texto.replace("\r\n", "\n")):
        lineas = [l.strip() for l in bloque.splitlines() if l.strip()]
        if len(lineas) < 3:
            continue
        m = _INDEED_URL.fullmatch(lineas[-1])
        if not m:
            continue
        job_id = m.group(1).lower()
        if job_id in vistos:
            continue
        vistos.add(job_id)
        titulo = lineas[0]
        # "Empresa - Ubicación": se corta en el ÚLTIMO " - " por si la
        # empresa trae guiones en el nombre.
        empresa, _, ubicacion = lineas[1].rpartition(" - ")
        if not empresa:
            empresa, ubicacion = lineas[1], None
        empresa = empresa.strip() or None
        ubicacion = (ubicacion or "").strip() or None
        if ubicacion and ubicacion.lower() in _INDEED_REMOTO:
            ubicacion = "Remoto"
        descripcion = [
            l for l in lineas[2:-1]
            if not l.lower().startswith(_INDEED_ETIQUETAS) and not _INDEED_SALARIO.search(l)
        ]
        resultados.append(
            {
                "tipo": "empleo",
                "source": "indeed",
                "external_id": job_id,
                "title": titulo,
                "company": empresa,
                "location": ubicacion,
                "url": f"https://co.indeed.com/viewjob?jk={job_id}",
                "description": " ".join(descripcion) or None,
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


# ------------------------------------------------------ Link manual (URL)

# Cada portal tiene su forma de identificar una vacante dentro del link.
# El id que sacamos aquí es EL MISMO que sacan los lectores de correo, así
# una vacante enviada a mano y la misma que llega por alerta dan la misma
# huella (dedup_key) y no se guardan dos veces.
_URL_PATRONES = [
    ("linkedin", "empleo", re.compile(r"linkedin\.com.*?(?:/jobs/view/(?:[^/?#]*-)?|[?&]currentJobId=)(\d+)")),
    ("indeed", "empleo", re.compile(r"indeed\.com/.*?[?&]v?jk=([0-9a-f]+)", re.IGNORECASE)),
    ("workana", "freelance", re.compile(r"workana\.com/job/([^/?#\s]+)")),
    ("greenhouse", "empleo", re.compile(r"greenhouse\.io/([^/?#]+)/jobs/(\d+)")),
    ("lever", "empleo", re.compile(r"jobs\.lever\.co/([^/?#]+)/([0-9a-f-]{36})", re.IGNORECASE)),
]
_URLS_LIMPIAS = {
    "linkedin": "https://www.linkedin.com/jobs/view/{id}/",
    "indeed": "https://co.indeed.com/viewjob?jk={id}",
    "workana": "https://www.workana.com/job/{id}",
}
_URL_EN_TEXTO = re.compile(r"https?://\S+")


def identificar_url(url: str) -> dict:
    """Reconoce de qué portal es un link de vacante y saca su id.

    Devuelve {source, tipo, external_id, url}. Si no reconoce el portal:
    source "manual", external_id None y el link tal cual (la huella será el
    link normalizado). NO abre el link: solo lee el texto del link.
    """
    url = url.strip().rstrip(".,;)>")
    for fuente, tipo, patron in _URL_PATRONES:
        m = patron.search(url)
        if not m:
            continue
        if fuente in ("greenhouse", "lever"):
            # El id solo es único dentro de la empresa: "empresa/id".
            external_id = f"{m.group(1).lower()}/{m.group(2).lower()}"
            limpia = url.split("?")[0].split("#")[0]
            if fuente == "greenhouse":
                limpia = f"https://boards.greenhouse.io/{external_id.replace('/', '/jobs/')}"
        else:
            external_id = m.group(1).lower() if fuente == "indeed" else m.group(1)
            external_id = external_id.rstrip("/")
            limpia = _URLS_LIMPIAS[fuente].format(id=external_id)
        return {"source": fuente, "tipo": tipo, "external_id": external_id, "url": limpia}
    if "computrabajo." in url:
        return {"source": "computrabajo", "tipo": "empleo", "external_id": None,
                "url": url.split("?")[0].split("#")[0]}
    return {"source": "manual", "tipo": "empleo", "external_id": None, "url": url}


def leer_mensaje_vacante(texto: str) -> tuple[str | None, str | None]:
    """De "/vacante <link> [título]" saca (link, título). Sin link → (None, None)."""
    texto = (texto or "").strip()
    texto = re.sub(r"^/vacante(@\w+)?", "", texto, flags=re.IGNORECASE).strip()
    m = _URL_EN_TEXTO.search(texto)
    if not m:
        return None, None
    titulo = (texto[: m.start()] + " " + texto[m.end():]).strip(" -—:\n\t")
    titulo = " ".join(titulo.split())
    return m.group(0), (titulo or None)


# --------------------------------------------------------------- Despacho

LECTORES = {
    "linkedin.com": ("linkedin", parse_linkedin),
    "workana.com": ("workana", parse_workana),
    "computrabajo.com": ("computrabajo", parse_computrabajo),
    "indeed.com": ("indeed", parse_indeed),
}


def elegir_lector(remitente: str):
    """Según el correo del remitente, devuelve (fuente, función) o (None, None)."""
    remitente = (remitente or "").lower()
    for dominio, (fuente, funcion) in LECTORES.items():
        if remitente.endswith(dominio):
            return fuente, funcion
    return None, None
