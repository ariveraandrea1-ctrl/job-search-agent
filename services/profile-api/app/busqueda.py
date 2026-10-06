"""Búsqueda por usuario (multiusuario, parte 4): palabras clave y categorías.

Cada usuario tiene sus propias palabras clave (ej. Andrea: qa, tester,
pruebas; otra persona: data, analista de datos, bi). Con ellas:
- se eligen las categorías de Get on Board que le sirven,
- se filtra el TÍTULO de cada vacante (en vez de la regla fija "solo QA").

Si el usuario no las configuró, se sugieren desde el "rol buscado" de la
entrevista y los cargos del CV. El usuario las ve y cambia con /preferencias.
Funciones puras (sin base de datos) para probarlas con pytest.
"""
import re
import unicodedata

MAX_PALABRAS = 12

# Categorías públicas de Get on Board (GET /api/v0/categories) y las
# palabras (sin tildes, en minúscula) que indican que una le sirve a alguien.
CATEGORIAS = {
    "sysadmin-devops-qa": ("SysAdmin / DevOps / QA",
                           ["qa", "tester", "test", "prueba", "calidad", "quality", "sdet",
                            "automatiza", "devops", "sysadmin", "cloud", "infraestructura"]),
    "programming": ("Programación",
                    ["desarroll", "developer", "programador", "backend", "frontend", "fullstack",
                     "full stack", "software", "python", "java", "javascript", "react", "node"]),
    "data-science-analytics": ("Data / Analytics",
                               ["data", "datos", "analytics", "analitica", "bi", "business intelligence",
                                "power bi", "sql", "etl"]),
    "machine-learning-ai": ("Machine Learning / IA",
                            ["machine learning", "ml", "ia", "inteligencia artificial", "ai", "llm"]),
    "mobile-developer": ("Desarrollo móvil", ["mobile", "movil", "android", "ios", "flutter"]),
    "design-ux": ("Diseño / UX", ["ux", "ui", "disen", "design", "producto digital"]),
    "customer-support": ("Atención al cliente",
                         ["atencion al cliente", "servicio al cliente", "customer", "soporte al cliente",
                          "pqrs", "call center"]),
    "technical-support": ("Soporte técnico", ["soporte tecnico", "mesa de ayuda", "helpdesk", "help desk"]),
    "cybersecurity": ("Ciberseguridad", ["seguridad", "security", "ciberseguridad", "pentest"]),
    "digital-marketing": ("Marketing digital", ["marketing", "seo", "redes sociales", "community"]),
    "sales": ("Ventas", ["ventas", "sales", "comercial"]),
    "hr": ("Personas / RRHH", ["recursos humanos", "rrhh", "talento", "recruiter", "reclutamiento"]),
    "operations-management": ("Operaciones / Gestión",
                              ["operaciones", "administrativ", "gestion", "project manager", "coordinador"]),
    "innovation-agile": ("Innovación / Agile", ["scrum", "agile", "agil", "product owner"]),
    "education-coaching": ("Educación", ["docente", "profesor", "tutor", "coach", "educacion"]),
    "advertising-media": ("Publicidad / Medios", ["publicidad", "medios", "contenido", "copywriter"]),
    "hardware-electronics": ("Hardware / Electrónica", ["hardware", "electronica", "electronico"]),
}

# Palabras que no sirven como palabra clave.
_VACIAS = {"de", "del", "la", "el", "en", "y", "o", "a", "para", "con", "los", "las", "un", "una",
           "jr", "junior", "sr", "senior", "semi", "trainee", "practicante", "remoto", "remota",
           "hibrido", "presencial", "medellin", "bogota", "colombia", "cualquiera", "rol", "cargo"}


def normalizar(texto: str | None) -> str:
    """Minúsculas y sin tildes: "Automatización" → "automatizacion"."""
    sin_tildes = unicodedata.normalize("NFD", texto or "")
    sin_tildes = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.lower().split())


def leer_palabras(texto: str | None) -> list[str]:
    """'QA, Tester / pruebas y calidad' → ['qa', 'tester', 'pruebas', 'calidad'].

    Separa por coma, punto y coma, barra, guion, salto de línea y la
    palabra "y" / "o"; quita palabras vacías y repetidas; máximo 12.
    """
    trozos = re.split(r"[,;/\n|]+|\s*-\s+|\s+y\s+|\s+o\s+", normalizar(texto))
    palabras = []
    for trozo in trozos:
        trozo = trozo.strip(" .-")
        if not trozo or trozo in _VACIAS or len(trozo) < 2:
            continue
        if trozo not in palabras:
            palabras.append(trozo)
    return palabras[:MAX_PALABRAS]


def sugerir_palabras(rol_buscado: str | None, cargos: list | None = None) -> list[str]:
    """Palabras iniciales desde el rol buscado (entrevista) y los cargos del CV."""
    texto = ", ".join([rol_buscado or ""] + [str(c) for c in (cargos or []) if c])
    palabras = []
    for frase in leer_palabras(texto):
        # Una frase larga ("desarrollador de software fullstack") casi nunca
        # aparece completa en un título: se parte en palabras sueltas.
        partes = [frase] if len(frase.split()) <= 3 else leer_palabras(frase.replace(" ", ","))
        # "qa engineer" no encontraría "QA Analyst": se agregan también las
        # palabras sueltas que son propias de un área (qa, tester, datos...).
        for palabra in frase.split():
            if palabra not in _VACIAS and _es_de_area(palabra):
                partes.append(palabra)
        for p in partes:
            if p not in palabras:
                palabras.append(p)
    return palabras[:MAX_PALABRAS]


def _coincide(texto_normalizado: str, palabra: str) -> bool:
    # Palabras cortas (qa, bi, ux, ia) deben ser palabra completa; las largas
    # basta con que empiecen igual ("automatiza" → automatización/automatizador).
    if len(palabra) <= 3:
        patron = rf"(?<![a-z0-9]){re.escape(palabra)}(?![a-z0-9])"
    else:
        patron = rf"(?<![a-z0-9]){re.escape(palabra)}"
    return re.search(patron, texto_normalizado) is not None


def _es_de_area(palabra: str) -> bool:
    return any(_coincide(palabra, d) for _, ds in CATEGORIAS.values() for d in ds if " " not in d)


def sugerir_categorias(palabras: list[str]) -> list[str]:
    """Categorías de Get on Board que corresponden a las palabras del usuario."""
    elegidas = []
    for cid, (_, disparadores) in CATEGORIAS.items():
        for palabra in palabras:
            p = normalizar(palabra)
            if any(_coincide(p, d) or _coincide(d, p) for d in disparadores):
                elegidas.append(cid)
                break
    return elegidas


def titulo_coincide(titulo: str | None, palabras: list[str]) -> bool:
    """¿El título de la vacante tiene alguna de las palabras del usuario?"""
    t = normalizar(titulo)
    return bool(palabras) and any(_coincide(t, normalizar(p)) for p in palabras)


def leer_comando_preferencias(texto: str | None) -> list[str] | None:
    """'/preferencias' → None (solo ver). '/preferencias qa, tester' → ['qa', 'tester']."""
    m = re.match(r"^\s*/preferencias(?:@\w+)?\s*(.*)$", texto or "", re.IGNORECASE | re.DOTALL)
    if not m or not m.group(1).strip():
        return None
    return leer_palabras(m.group(1))


def texto_preferencias(palabras: list[str], categorias: list[str], cambiadas: bool = False) -> str:
    inicio = "✅ Listo, actualicé tu búsqueda.\n\n" if cambiadas else "🔎 Tu búsqueda de vacantes\n\n"
    if not palabras:
        return (inicio + "Todavía no tienes palabras clave. Envíame tu CV o escribe, por ejemplo:\n"
                "/preferencias analista de datos, bi, sql")
    nombres = [CATEGORIAS[c][0] for c in categorias if c in CATEGORIAS]
    return (inicio
            + "Palabras clave: " + ", ".join(palabras) + "\n"
            + "Categorías de Get on Board: " + (", ".join(nombres) if nombres else "ninguna (revisa tus palabras)") + "\n\n"
            + "Solo te llegan vacantes cuyo título tenga alguna de esas palabras.\n"
            + "Para cambiarlas escribe /preferencias y la lista separada por comas. Ejemplo:\n"
            + "/preferencias qa, tester, pruebas, calidad")


def filtrar_por_palabras(ofertas: list[dict], palabras: list[str]) -> tuple[list[dict], int]:
    """Deja solo las ofertas cuyo título tiene alguna palabra del usuario (BUG-28).

    Sin palabras configuradas no filtra (mejor que perder todo).
    Devuelve (las que sirven, cuántas se descartaron).
    """
    if not palabras:
        return list(ofertas), 0
    sirven = [o for o in ofertas if titulo_coincide(o.get("title"), palabras)]
    return sirven, len(ofertas) - len(sirven)
