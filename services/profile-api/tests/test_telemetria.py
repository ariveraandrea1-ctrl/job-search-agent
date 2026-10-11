"""Pruebas de la telemetría de IA (app/telemetria.py)."""
from app.telemetria import costo_usd, resumen, texto_resumen

PRECIOS = {"openai/gpt-oss-120b": [0.15, 0.60]}


def test_costo_con_precio_configurado():
    # 1M de entrada a 0.15 + 0.5M de salida a 0.60 = 0.45
    assert costo_usd("openai/gpt-oss-120b", 1_000_000, 500_000, PRECIOS) == 0.45


def test_costo_cero_sin_precio_o_sin_tokens():
    assert costo_usd("gemini-x", 1000, 1000, PRECIOS) == 0
    assert costo_usd("openai/gpt-oss-120b", None, None, PRECIOS) == 0


LLAMADAS = [
    {"tarea": "puntaje", "proveedor": "groq", "ok": True, "fallback": False, "latencia_ms": 800,
     "tokens_entrada": 1000, "tokens_salida": 200, "costo_usd": 0},
    {"tarea": "puntaje", "proveedor": "gemini", "ok": True, "fallback": True, "latencia_ms": 2400,
     "tokens_entrada": 900, "tokens_salida": 150, "costo_usd": 0},
    {"tarea": "cv", "proveedor": "groq", "ok": False, "fallback": False, "latencia_ms": 1200,
     "tokens_entrada": 3000, "tokens_salida": 900, "costo_usd": 0.001},
]


def test_resumen_cuenta_proveedores_errores_y_fallback():
    r = resumen(LLAMADAS)
    assert r["llamadas"] == 3
    assert r["por_proveedor"] == {"groq": 2, "gemini": 1}
    assert r["por_tarea"] == {"puntaje": 2, "cv": 1}
    assert r["errores"] == 1 and r["fallback"] == 1
    assert r["latencia_ms_mediana"] == 1200 and r["latencia_ms_max"] == 2400
    assert r["tokens"] == 6150


def test_resumen_vacio():
    assert resumen([]) == {"llamadas": 0}
    assert "no hubo llamadas" in texto_resumen({"llamadas": 0}, 7)


def test_texto_resumen_muestra_porcentajes():
    texto = texto_resumen(resumen(LLAMADAS), 7)
    assert "Respaldo (Gemini porque Groq falló): 1 (33%)" in texto
