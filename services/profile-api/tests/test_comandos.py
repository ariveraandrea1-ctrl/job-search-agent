"""Pruebas de los comandos del radar en Telegram (app/comandos.py)."""
import pytest

from datetime import datetime, timedelta, timezone

from app import comandos
from app.comandos import (
    AYUDA,
    leer_comando,
    texto_antiguedad,
    texto_detalle,
    texto_lista,
    texto_resumen_diario,
)


@pytest.mark.parametrize("texto, esperado", [
    ("/mejores", ("mejores", None)),
    ("/detalle 12", ("detalle", 12)),
    ("/detalle #12", ("detalle", 12)),
    ("/guardar@mi_bot 7", ("guardar", 7)),
    ("  /DESCARTAR 3", ("descartar", 3)),
    ("/detalle", ("detalle", None)),
    ("/perfil", (None, None)),
    ("hola", (None, None)),
    ("", (None, None)),
])
def test_leer_comando(texto, esperado):
    assert leer_comando(texto) == esperado


VACANTE = {"numero": 12, "title": "Analista QA Jr", "company": "Empresa Uno",
           "location": "Medellín", "source": "getonbrd", "url": "https://ejemplo.com/12",
           "status": "nueva", "score": 30,
           "analysis": {"puntaje_ia": 80, "ingles": "avanzado", "nivel_vacante": "junior",
                        "razones_a_favor": ["Pide pytest"], "razones_en_contra": ["Pide C1"],
                        "senales_alerta": [], "resumen": "Buen rol, pero inglés alto.",
                        "reglas_aplicadas": ["Tope 35 porque exige inglés avanzado"]}}


def test_lista_muestra_numero_puntaje_y_ayuda():
    texto = texto_lista("Mejores:", [VACANTE, {**VACANTE, "numero": 13, "score": None,
                                               "company": None, "location": None}], "vacío")
    assert "#12 · 30 pts · Analista QA Jr (Empresa Uno — Medellín)" in texto
    assert "#13 · sin puntaje aún · Analista QA Jr" in texto
    assert "\n   https://ejemplo.com/12" in texto  # cada vacante trae su link
    assert "/detalle 12" in texto


def test_lista_vacia_da_el_mensaje_de_vacio():
    assert texto_lista("Mejores:", [], "No hay nada") == "No hay nada"


def test_detalle_explica_puntaje_ingles_y_regla():
    texto = texto_detalle(VACANTE)
    assert "Puntaje: 30/100" in texto
    assert "Inglés que piden: avanzado" in texto
    assert "✅ Pide pytest" in texto and "➖ Pide C1" in texto
    assert "(la IA le había dado 80)" in texto
    assert "/guardar 12" in texto and "Señales de alerta" not in texto


def test_detalle_sin_puntaje_lo_avisa():
    texto = texto_detalle({**VACANTE, "score": None, "analysis": None})
    assert "todavía no la ha revisado la IA" in texto


def test_ayuda_lista_todos_los_comandos():
    for c in ["/mejores", "/nuevas", "/guardadas", "/detalle", "/guardar", "/descartar"]:
        assert c in AYUDA


AHORA = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def test_antiguedad_usa_la_fecha_de_publicacion_si_existe():
    publicada = (AHORA - timedelta(days=2, hours=3)).timestamp()
    assert texto_antiguedad({"published_at": publicada}, AHORA) == "publicada hace 2 días"


def test_antiguedad_sin_fecha_de_publicacion_usa_cuando_llego():
    assert texto_antiguedad({"created_at": AHORA - timedelta(hours=5)}, AHORA) == "llegó hace 5 h"
    assert texto_antiguedad({"created_at": AHORA - timedelta(days=1)}, AHORA) == "llegó hace 1 día"
    assert texto_antiguedad({"created_at": AHORA}, AHORA) == "llegó hace un momento"
    assert texto_antiguedad({}, AHORA) == ""



def _v(numero, score=None, source="linkedin", tipo="empleo", alertas=None):
    return {"numero": numero, "title": f"Vacante {numero}", "company": None, "location": None,
            "source": source, "tipo": tipo, "score": score,
            "analysis": {"senales_alerta": alertas or []}}


def test_resumen_sin_vacantes():
    assert "no llegaron vacantes nuevas" in texto_resumen_diario([], 0)


def test_resumen_cuenta_por_fuente_ordena_y_separa_alertas():
    vacantes = [_v(1, 40), _v(2, 90, source="getonbrd"), _v(3, None),
                _v(4, 95, alertas=["Pide abrir cuenta bancaria"]),
                _v(5, 60, source="workana", tipo="freelance")]
    texto = texto_resumen_diario(vacantes, pendientes=1,
                                 nombres_fuentes={"linkedin": "LinkedIn", "getonbrd": "Get on Board",
                                                  "workana": "Workana"})
    assert "Llegaron 5 vacante(s): LinkedIn 3, Get on Board 1, Workana 1." in texto
    assert "⚡ 1 proyecto(s) freelance" in texto
    assert "La IA aún no puntúa 1" in texto
    mejores = texto.split("🏆 Las mejores de hoy:")[1].split("⚠️")[0]
    # La #4 tiene alerta: NO va en las mejores aunque tenga 95.
    assert mejores.index("#2 ·") < mejores.index("#5 ·") < mejores.index("#1 ·")
    assert "#4" not in mejores
    assert "⚠️ Con señales de alerta (cuidado):\n#4 · Vacante 4" in texto
    assert "/detalle 2" in texto


# ---------------------------------------------- /pausar y /reanudar (multiusuario)

def test_pausar_y_reanudar_son_comandos_sin_numero():
    assert comandos.leer_comando("/pausar") == ("pausar", None)
    assert comandos.leer_comando("/reanudar") == ("reanudar", None)
    assert comandos.leer_comando("/PAUSAR") == ("pausar", None)


def test_ayuda_menciona_pausar_y_reanudar():
    assert "/pausar" in comandos.AYUDA and "/reanudar" in comandos.AYUDA


def test_textos_de_estado_explican_como_volver():
    assert "/reanudar" in comandos.TEXTOS_ESTADO_USUARIO["pausado"]
    assert set(comandos.TEXTOS_ESTADO_USUARIO) == {"pausado", "activo"}


# ------------------------------------------------ resumen por correo

@pytest.mark.parametrize("entrada, esperado", [
    ("andrea@gmail.com", "andrea@gmail.com"),
    ("  Andrea.Rivera@Gmail.COM ", "andrea.rivera@gmail.com"),
    ("<andrea@correo.co>", "andrea@correo.co"),
    ("andrea arroba gmail", None),
    ("", None),
    (None, None),
])
def test_email_valido(entrada, esperado):
    assert comandos.email_valido(entrada) == esperado


def test_texto_correo_trae_el_resumen_y_como_pausar():
    texto = comandos.texto_correo("☀️ Buenos días. Resumen…")
    assert texto.startswith("☀️ Buenos días") and "/pausar" in texto
