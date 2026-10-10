"""Pruebas de usuarios e invitaciones (funciones puras, sin base de datos).

Correr desde services/profile-api con:  python3 -m pytest tests -v
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.usuarios import (
    ALFABETO,
    INVITACION_DIAS,
    generar_codigo,
    leer_codigo_start,
    avisa_radar,
    revisar_invitacion,
    vence,
)

AHORA = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)


def test_codigo_tiene_8_caracteres_sin_letras_confusas():
    for _ in range(200):
        codigo = generar_codigo()
        assert len(codigo) == 8
        assert set(codigo) <= set(ALFABETO)
        assert not set(codigo) & set("0O1IL")


def test_codigos_no_se_repiten():
    codigos = {generar_codigo() for _ in range(1000)}
    assert len(codigos) == 1000


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("/start AB12CD34", "AB12CD34"),
        ("/start ab12cd34", "AB12CD34"),       # minúsculas → mayúsculas
        ("  /start   AB12CD34  ", "AB12CD34"),  # espacios de más
        ("/start AB12-CD34", "AB12CD34"),      # guion opcional
        ("/start@MiBot AB12CD34", "AB12CD34"),  # así llega en grupos
        ("/start", None),
        ("hola", None),
        ("/perfil", None),
        ("", None),
        (None, None),
    ],
)
def test_leer_codigo_start(texto, esperado):
    assert leer_codigo_start(texto) == esperado


def _inv(**cambios):
    base = {"code": "AB12CD34", "used_by": None, "expires_at": vence(AHORA - timedelta(days=1))}
    base.update(cambios)
    return base


def test_invitacion_valida():
    assert revisar_invitacion(_inv(), AHORA) is None


def test_invitacion_inexistente():
    assert revisar_invitacion(None, AHORA) == "no_existe"


def test_invitacion_usada_no_sirve_otra_vez():
    assert revisar_invitacion(_inv(used_by=123), AHORA) == "usada"


def test_invitacion_vencida():
    creada = AHORA - timedelta(days=INVITACION_DIAS)  # justo en el límite
    assert revisar_invitacion(_inv(expires_at=vence(creada)), AHORA) == "vencida"


# BUG-34: con el radar en pausa no se avisa, aunque haya vacantes nuevas.
def test_avisa_si_hay_nuevas_y_esta_activo():
    assert avisa_radar("activo", 2) is True


def test_no_avisa_si_esta_en_pausa():
    assert avisa_radar("pausado", 2) is False


def test_no_avisa_si_no_hay_nuevas():
    assert avisa_radar("activo", 0) is False
