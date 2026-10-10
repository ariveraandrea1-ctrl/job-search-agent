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


# Observación E2E-06: la entrevista aceptó "1000000" como aspiración salarial sin avisar.
from app import usuarios as u


@pytest.mark.parametrize("respuesta,esperado", [
    ("3.000.000", (3_000_000, "COP")),
    ("3,000,000", (3_000_000, "COP")),
    ("4 millones", (4_000_000, "COP")),
    ("entre 3,5 y 4 millones", (3_500_000, "COP")),
    ("10000 USD", (10_000, "USD")),
    ("2k dólares", (2_000, "USD")),
    ("a convenir", None),
    ("4", None),
])
def test_leer_salario(respuesta, esperado):
    assert u.leer_salario(respuesta) == esperado


@pytest.mark.parametrize("respuesta", ["1000000", "1.000.000", "200 USD"])
def test_avisa_si_el_salario_es_muy_bajo(respuesta):
    aviso = u.revisar_salario(respuesta)
    assert aviso is not None and "muy baja" in aviso and "/corregir salario" in aviso


@pytest.mark.parametrize("respuesta", ["10000 USD", "80.000.000"])
def test_avisa_si_el_salario_es_muy_alto(respuesta):
    assert "muy alta" in u.revisar_salario(respuesta)


@pytest.mark.parametrize("respuesta", ["3.000.000", "4 millones", "2500 USD", "a convenir", "4"])
def test_no_avisa_si_el_salario_se_ve_bien(respuesta):
    assert u.revisar_salario(respuesta) is None
