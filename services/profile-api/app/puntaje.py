"""Puntaje de vacantes con IA (Semana 6).

Funciones PURAS (sin base de datos) para poder probarlas con pytest:

- armar_resumen_perfil(): resume el perfil del CV + preferencias en texto.
- armar_texto_vacante(): arma el texto de una vacante para la IA.
- leer_respuesta_puntaje(): revisa el JSON que devuelve la IA, lo limpia y
  aplica REGLAS FIJAS (topes de puntaje) que no dependen de la IA.

El flujo es: profile-api arma la pregunta → n8n la manda a ai-model-router
→ n8n devuelve la respuesta a profile-api → se valida y se guarda.
"""
import json
import re

PROMPT_VERSION = "puntaje-v1"

PROMPT_PUNTAJE = """Eres un asistente que evalúa qué tan bien encaja una vacante de empleo (o proyecto freelance) con el perfil de una persona que busca trabajo.

Reglas obligatorias:
1. Usa SOLO la información del perfil y de la vacante. No inventes datos.
2. Si a la vacante le falta información (por ejemplo, no tiene descripción), dilo en "razones_en_contra" y no supongas lo que no está.
3. Responde ÚNICAMENTE con un JSON válido, sin texto antes ni después y sin ```.
4. Escribe en español.

Formato exacto de la respuesta:
{
  "puntaje": 0,
  "ingles": "desconocido",
  "nivel_vacante": "desconocido",
  "razones_a_favor": [],
  "razones_en_contra": [],
  "senales_alerta": [],
  "resumen": ""
}

Cómo llenar cada campo:
- "puntaje": número entero de 0 a 100. Qué tan bien encaja la vacante con el perfil y sus preferencias (rol, nivel de experiencia, habilidades, ciudad/modalidad, salario si se conoce).
  Guía: 80-100 encaja muy bien; 60-79 encaja bien con alguna diferencia; 40-59 encaje parcial; 0-39 encaja poco.
  Si la vacante pide bastante más experiencia de la que tiene la persona (por ejemplo, 3 o más años, o nivel Senior), baja mucho el puntaje.
- "ingles": nivel de inglés que EXIGE la vacante. Uno de: "no_requerido", "basico", "intermedio", "avanzado", "desconocido".
  "avanzado" si pide B2/C1/C2, inglés fluido, avanzado, o si la entrevista o el trabajo es en inglés. "intermedio" si pide B1 o intermedio. "basico" si pide básico, técnico o lectura de documentación. "no_requerido" solo si la vacante dice claramente que no se necesita. Si no dice nada, "desconocido". Si el aviso está escrito en inglés, al menos "intermedio".
- "nivel_vacante": uno de "sin_experiencia", "junior", "semi_senior", "senior", "desconocido", según lo que pide la vacante.
- "razones_a_favor": hasta 3 frases cortas de por qué encaja.
- "razones_en_contra": hasta 3 frases cortas de por qué no encaja o qué falta.
- "senales_alerta": posibles estafas o riesgos. Inclúyelas SOLO si la vacante las muestra: pedir documentos de identidad o selfies para "verificación" (KYC) antes de contratar, pedir abrir o probar cuentas bancarias, billeteras o tarjetas, pedir dinero o pagar por capacitación, pagos o comunicación fuera de la plataforma, sueldo irreal para el trabajo pedido, empresa sin nombre con promesas exageradas. Si no hay, [].
- "resumen": una frase corta (máximo 20 palabras) para mostrar en Telegram."""

INGLES_VALIDOS = {"no_requerido", "basico", "intermedio", "avanzado", "desconocido"}
NIVELES_VALIDOS = {"sin_experiencia", "junior", "semi_senior", "senior", "desconocido"}

# Reglas fijas: topes de puntaje que se aplican DESPUÉS de la IA.
TOPE_INGLES = {"avanzado": 35, "intermedio": 60}
TOPE_NIVEL = {"senior": 40}
TOPE_ALERTAS = 20


class RespuestaInvalida(ValueError):
    """La IA devolvió algo que no se puede usar como puntaje."""


def _lista_textos(valor, maximo: int = 3) -> list[str]:
    if not isinstance(valor, list):
        return []
    textos = [" ".join(str(v).split()) for v in valor if str(v).strip()]
    return textos[:maximo]


def armar_resumen_perfil(perfil: dict, preferencias: dict) -> str:
    """Resume el perfil del CV y las preferencias de la entrevista en texto."""
    perfil = perfil or {}
    lineas = []
    cargos = (perfil.get("perfil") or {}).get("cargos") or []
    if cargos:
        lineas.append("Cargos: " + ", ".join(cargos))
    resumen = (perfil.get("perfil") or {}).get("resumen")
    if resumen:
        lineas.append("Resumen: " + " ".join(str(resumen).split())[:600])
    experiencia = [
        f"{e.get('cargo')} en {e.get('empresa')} ({e.get('inicio') or '?'} a {e.get('fin') or '?'})"
        for e in perfil.get("experiencia") or [] if e.get("cargo") or e.get("empresa")
    ]
    if experiencia:
        lineas.append("Experiencia laboral: " + "; ".join(experiencia))
    proyectos = [p.get("nombre") for p in perfil.get("proyectos") or [] if p.get("nombre")]
    if proyectos:
        lineas.append("Proyectos: " + "; ".join(proyectos))
    habilidades = perfil.get("habilidades") or {}
    for clave, nombre in [("qa", "Habilidades QA"), ("automatizacion", "Automatización"),
                          ("bases_de_datos", "Bases de datos"), ("herramientas", "Herramientas"),
                          ("profesionales", "Otras competencias")]:
        if habilidades.get(clave):
            lineas.append(f"{nombre}: " + ", ".join(habilidades[clave]))
    idiomas = [f"{i.get('idioma')} ({i.get('nivel') or 'nivel no indicado'})"
               for i in perfil.get("idiomas") or [] if i.get("idioma")]
    if idiomas:
        lineas.append("Idiomas: " + ", ".join(idiomas))
    if preferencias:
        lineas.append("Preferencias de búsqueda:")
        for tema, respuesta in preferencias.items():
            lineas.append(f"- {tema}: " + " ".join(str(respuesta).split())[:200])
    return "\n".join(lineas) or "(perfil vacío)"


def armar_texto_vacante(vacante: dict, maximo_descripcion: int = 3000) -> str:
    """Arma el texto de una vacante para la IA."""
    lineas = [
        f"Título: {vacante.get('title')}",
        f"Tipo: {vacante.get('tipo')}",
        f"Empresa: {vacante.get('company') or 'no indicada'}",
        f"Ubicación: {vacante.get('location') or 'no indicada'}",
        f"Fuente: {vacante.get('source')}",
    ]
    raw = vacante.get("raw") or {}
    if raw.get("nivel"):
        lineas.append(f"Nivel según el portal: {raw['nivel']}")
    if raw.get("min_salary") or raw.get("max_salary"):
        lineas.append(f"Salario según el portal (USD/mes): {raw.get('min_salary')} - {raw.get('max_salary')}")
    descripcion = " ".join(str(vacante.get("description") or "").split())
    if descripcion:
        if len(descripcion) > maximo_descripcion:
            descripcion = descripcion[:maximo_descripcion] + "…"
        lineas.append(f"Descripción: {descripcion}")
    else:
        lineas.append("Descripción: (la fuente no trae descripción; evalúa solo con lo anterior)")
    return "\n".join(lineas)


def armar_pregunta(perfil: dict, preferencias: dict, vacante: dict) -> str:
    """El "user_text" que n8n le manda a ai-model-router."""
    return ("PERFIL DE LA PERSONA:\n" + armar_resumen_perfil(perfil, preferencias)
            + "\n\nVACANTE:\n" + armar_texto_vacante(vacante))


def leer_respuesta_puntaje(texto: str) -> dict:
    """Valida y limpia el JSON de la IA, y aplica las reglas fijas.

    Lanza RespuestaInvalida si no se puede usar.
    """
    texto = (texto or "").strip()
    # Por si la IA envolvió el JSON en ```json ... ```
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto).strip()
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise RespuestaInvalida(f"La IA no devolvió un JSON válido: {error.msg}")
    if not isinstance(datos, dict):
        raise RespuestaInvalida("La IA devolvió JSON, pero no es un objeto {...}.")
    try:
        puntaje = int(round(float(datos.get("puntaje"))))
    except (TypeError, ValueError):
        raise RespuestaInvalida("Falta el puntaje o no es un número.")
    puntaje = max(0, min(100, puntaje))

    ingles = str(datos.get("ingles") or "desconocido").strip().lower()
    ingles = ingles if ingles in INGLES_VALIDOS else "desconocido"
    nivel = str(datos.get("nivel_vacante") or "desconocido").strip().lower().replace(" ", "_")
    nivel = nivel if nivel in NIVELES_VALIDOS else "desconocido"
    alertas = _lista_textos(datos.get("senales_alerta"), maximo=5)

    # Reglas fijas: el puntaje no puede pasar de estos topes.
    puntaje_ia = puntaje
    topes = []
    if ingles in TOPE_INGLES:
        topes.append((TOPE_INGLES[ingles], f"exige inglés {ingles}"))
    if nivel in TOPE_NIVEL:
        topes.append((TOPE_NIVEL[nivel], f"vacante {nivel}"))
    if alertas:
        topes.append((TOPE_ALERTAS, "tiene señales de alerta"))
    reglas = []
    for tope, motivo in topes:
        if puntaje > tope:
            puntaje = tope
            reglas.append(f"Tope {tope} porque {motivo}")

    return {
        "puntaje": puntaje,
        "puntaje_ia": puntaje_ia,
        "ingles": ingles,
        "nivel_vacante": nivel,
        "razones_a_favor": _lista_textos(datos.get("razones_a_favor")),
        "razones_en_contra": _lista_textos(datos.get("razones_en_contra")),
        "senales_alerta": alertas,
        "resumen": " ".join(str(datos.get("resumen") or "").split())[:200],
        "reglas_aplicadas": reglas,
    }


def sin_datos(titulo: str | None, descripcion: str | None) -> bool:
    """Vacante sin título real ni descripción (ej. /vacante solo con el link).

    La IA no tiene nada que evaluar: no se le manda y queda marcada "sin datos"
    (observación E2E-27: la #367 recibió 15 pts sin saber nada de ella)."""
    sin_titulo = not (titulo or "").strip() or (titulo or "").strip().endswith("(sin título)")
    return sin_titulo and not (descripcion or "").strip()
