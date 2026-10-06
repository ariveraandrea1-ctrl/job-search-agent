"""Pruebas de la búsqueda por usuario (app/busqueda.py) y su uso en Get on Board."""
import pytest

from app import busqueda as b
from app.parsers import getonbrd_sirve


def test_leer_palabras_separa_limpia_y_quita_repetidas():
    assert b.leer_palabras("QA, Tester / pruebas y calidad; QA") == ["qa", "tester", "pruebas", "calidad"]


def test_leer_palabras_quita_tildes_y_palabras_vacias():
    assert b.leer_palabras("Automatización, de, Junior, remoto") == ["automatizacion"]


def test_maximo_15_palabras():
    assert len(b.leer_palabras(",".join(f"palabra{i}" for i in range(20)))) == 15


def test_sugerir_desde_rol_y_cargos_agrega_palabras_de_area():
    palabras = b.sugerir_palabras("QA Engineer, Tester manual", ["Analista de Pruebas"])
    assert {"qa", "tester", "pruebas"} <= set(palabras)


def test_sugerir_parte_frases_largas():
    palabras = b.sugerir_palabras("Desarrollador de software fullstack- IA Engineering")
    assert "desarrollador" in palabras and "fullstack" in palabras


@pytest.mark.parametrize("palabras, categoria", [
    (["qa", "tester"], "sysadmin-devops-qa"),
    (["analista de datos", "bi"], "data-science-analytics"),
    (["desarrollador", "python"], "programming"),
    (["atencion al cliente"], "customer-support"),
])
def test_sugerir_categorias(palabras, categoria):
    assert categoria in b.sugerir_categorias(palabras)


def test_categorias_de_qa_no_incluyen_data():
    assert b.sugerir_categorias(["qa", "tester", "pruebas"]) == ["sysadmin-devops-qa"]


@pytest.mark.parametrize("titulo, esperado", [
    ("QA Analyst", True),
    ("Analista de Automatización de Pruebas", True),   # prefijo + sin tildes
    ("Qatar Airways Sales", False),                     # "qa" debe ser palabra completa
    ("Data Analyst", False),
])
def test_titulo_coincide(titulo, esperado):
    assert b.titulo_coincide(titulo, ["qa", "automatiza", "pruebas"]) is esperado


def test_sin_palabras_no_coincide_nada():
    assert b.titulo_coincide("QA Analyst", []) is False


def test_comando_preferencias():
    assert b.leer_comando_preferencias("/preferencias") is None
    assert b.leer_comando_preferencias("/preferencias Data, BI") == ["data", "bi"]


def test_texto_preferencias_explica_como_cambiar():
    texto = b.texto_preferencias(["qa"], ["sysadmin-devops-qa"])
    assert "qa" in texto and "SysAdmin / DevOps / QA" in texto and "/preferencias" in texto


_BASE = {"lang": "es", "remote_modality": "fully_remote", "countries": [],
         "seniority": {"data": {"id": 2}}}


def test_getonbrd_filtra_por_palabras_del_usuario():
    data = {**_BASE, "title": "Data Analyst Jr"}
    assert getonbrd_sirve(data, ["data"]) is True
    assert getonbrd_sirve(data, ["qa", "tester"]) is False


def test_getonbrd_sin_palabras_usa_regla_vieja_de_qa():
    assert getonbrd_sirve({**_BASE, "title": "QA Tester"}) is True
    assert getonbrd_sirve({**_BASE, "title": "Data Analyst"}) is False


# ------------------------------------------- BUG-28: filtro de correo

def test_filtrar_por_palabras_saca_las_que_no_tienen_nada_que_ver():
    ofertas = [{"title": "Analista de Nómina"}, {"title": "QA Tester Jr"},
               {"title": "Analista de Calidad de Software"}, {"title": "Auxiliar Contable"}]
    sirven, descartadas = b.filtrar_por_palabras(ofertas, ["qa", "tester", "calidad"])
    assert [o["title"] for o in sirven] == ["QA Tester Jr", "Analista de Calidad de Software"]
    assert descartadas == 2


def test_filtrar_sin_palabras_no_descarta_nada():
    ofertas = [{"title": "Analista de Nómina"}]
    assert b.filtrar_por_palabras(ofertas, []) == (ofertas, 0)
