"""Pruebas del puntaje con IA (app/puntaje.py). Datos inventados."""
import json

import pytest

from app.puntaje import (
    RespuestaInvalida,
    armar_pregunta,
    armar_resumen_perfil,
    armar_texto_vacante,
    leer_respuesta_puntaje,
)

PERFIL = {
    "perfil": {"cargos": ["QA Engineer Jr"], "resumen": "QA en formación."},
    "experiencia": [{"empresa": "Empresa Uno", "cargo": "Asesora", "inicio": "2019-01", "fin": "2024-12"}],
    "proyectos": [{"nombre": "App de pruebas"}],
    "habilidades": {"qa": ["casos de prueba"], "automatizacion": ["Python", "pytest"],
                    "bases_de_datos": ["SQL"], "herramientas": ["Postman"]},
    "idiomas": [{"idioma": "Inglés", "nivel": "básico"}],
}
PREFERENCIAS = {"modalidad": "Remoto o híbrido en Medellín", "salario": "2.500.000"}


def _ia(**campos):
    base = {"puntaje": 80, "ingles": "no_requerido", "nivel_vacante": "junior",
            "razones_a_favor": ["a"], "razones_en_contra": [], "senales_alerta": [], "resumen": "ok"}
    base.update(campos)
    return json.dumps(base)


def test_resumen_perfil_incluye_lo_importante():
    texto = armar_resumen_perfil(PERFIL, PREFERENCIAS)
    for parte in ["QA Engineer Jr", "pytest", "Inglés (básico)", "modalidad: Remoto"]:
        assert parte in texto


def test_texto_vacante_sin_descripcion_lo_avisa():
    texto = armar_texto_vacante({"title": "QA Jr", "tipo": "empleo", "source": "linkedin"})
    assert "no trae descripción" in texto
    assert "Empresa: no indicada" in texto


def test_texto_vacante_recorta_descripcion_larga():
    texto = armar_texto_vacante({"title": "QA", "description": "x " * 5000}, maximo_descripcion=100)
    assert texto.endswith("…")


def test_pregunta_tiene_perfil_y_vacante():
    pregunta = armar_pregunta(PERFIL, PREFERENCIAS, {"title": "Analista QA"})
    assert pregunta.startswith("PERFIL DE LA PERSONA:") and "VACANTE:\nTítulo: Analista QA" in pregunta


def test_respuesta_normal_se_respeta():
    r = leer_respuesta_puntaje(_ia(puntaje=82))
    assert r["puntaje"] == 82 and r["reglas_aplicadas"] == []


def test_acepta_json_envuelto_en_backticks():
    r = leer_respuesta_puntaje("```json\n" + _ia(puntaje=70) + "\n```")
    assert r["puntaje"] == 70


def test_tope_por_ingles_avanzado():
    r = leer_respuesta_puntaje(_ia(puntaje=90, ingles="avanzado"))
    assert r["puntaje"] == 35 and r["puntaje_ia"] == 90
    assert r["reglas_aplicadas"] == ["Tope 35 porque exige inglés avanzado"]


def test_tope_por_senior_y_por_alertas_gana_el_menor():
    r = leer_respuesta_puntaje(_ia(puntaje=75, nivel_vacante="senior",
                                   senales_alerta=["Pide abrir una cuenta bancaria"]))
    assert r["puntaje"] == 20
    assert len(r["reglas_aplicadas"]) == 2


def test_puntaje_fuera_de_rango_y_valores_raros_se_limpian():
    r = leer_respuesta_puntaje(_ia(puntaje=150, ingles="FLUIDO", nivel_vacante="Semi Senior"))
    assert r["puntaje"] == 100
    assert r["ingles"] == "desconocido"
    assert r["nivel_vacante"] == "semi_senior"


@pytest.mark.parametrize("texto", ["", "hola", "[1, 2]", json.dumps({"ingles": "basico"}),
                                   json.dumps({"puntaje": "alto"})])
def test_respuestas_invalidas_se_rechazan(texto):
    with pytest.raises(RespuestaInvalida):
        leer_respuesta_puntaje(texto)
