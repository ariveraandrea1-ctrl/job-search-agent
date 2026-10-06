"""Telemetría de IA: un registro por cada vez que se usa la IA (tabla ai_calls).

La especificación (sección 8): "Se registran proveedor, alias, prompt,
tokens, latencia, costo y fallback". Este módulo tiene la parte pura
(costo estimado y resumen) para probarla con pytest.

Costo: se calcula con precios por MILLÓN de tokens que se configuran en
.env (AI_PRECIOS_JSON, ej. {"openai/gpt-oss-120b": [0.15, 0.60]} =
entrada, salida). Sin precios configurados el costo es 0: hoy Groq y
Gemini se usan en sus planes gratuitos.
"""
import json
import os


def precios() -> dict:
    try:
        return json.loads(os.environ.get("AI_PRECIOS_JSON") or "{}")
    except json.JSONDecodeError:
        return {}


def costo_usd(modelo: str | None, tokens_entrada: int | None, tokens_salida: int | None,
              tabla: dict | None = None) -> float:
    """Costo estimado en dólares de UNA llamada (0 si no hay precio para el modelo)."""
    tabla = precios() if tabla is None else tabla
    entrada, salida = tabla.get(modelo or "", [0, 0])
    return round(((tokens_entrada or 0) * entrada + (tokens_salida or 0) * salida) / 1_000_000, 6)


def resumen(llamadas: list[dict]) -> dict:
    """Totales de una lista de llamadas: por proveedor, errores, fallback, latencia, tokens, costo."""
    total = len(llamadas)
    if total == 0:
        return {"llamadas": 0}
    lat = sorted(l["latencia_ms"] for l in llamadas if l.get("latencia_ms") is not None)
    por_proveedor: dict[str, int] = {}
    por_tarea: dict[str, int] = {}
    for l in llamadas:
        por_proveedor[l.get("proveedor") or "?"] = por_proveedor.get(l.get("proveedor") or "?", 0) + 1
        por_tarea[l.get("tarea") or "?"] = por_tarea.get(l.get("tarea") or "?", 0) + 1
    return {
        "llamadas": total,
        "por_proveedor": por_proveedor,
        "por_tarea": por_tarea,
        "errores": sum(1 for l in llamadas if not l.get("ok")),
        "fallback": sum(1 for l in llamadas if l.get("fallback")),
        "latencia_ms_mediana": lat[len(lat) // 2] if lat else None,
        "latencia_ms_max": lat[-1] if lat else None,
        "tokens": sum((l.get("tokens_entrada") or 0) + (l.get("tokens_salida") or 0) for l in llamadas),
        "costo_usd": round(sum(l.get("costo_usd") or 0 for l in llamadas), 4),
    }


def texto_resumen(r: dict, dias: int) -> str:
    if not r.get("llamadas"):
        return f"📊 IA: no hubo llamadas en los últimos {dias} días."
    prov = ", ".join(f"{k} {v}" for k, v in sorted(r["por_proveedor"].items()))
    tareas = ", ".join(f"{k} {v}" for k, v in sorted(r["por_tarea"].items()))
    pct = lambda n: f"{round(100 * n / r['llamadas'])}%"  # noqa: E731
    return (f"📊 Uso de la IA (últimos {dias} días)\n\n"
            f"Llamadas: {r['llamadas']} ({tareas})\n"
            f"Proveedor: {prov}\n"
            f"Respaldo (Gemini porque Groq falló): {r['fallback']} ({pct(r['fallback'])})\n"
            f"Respuestas inválidas: {r['errores']} ({pct(r['errores'])})\n"
            f"Latencia: mediana {r['latencia_ms_mediana']} ms, máxima {r['latencia_ms_max']} ms\n"
            f"Tokens: {r['tokens']:,}\n"
            f"Costo estimado: US$ {r['costo_usd']}")
