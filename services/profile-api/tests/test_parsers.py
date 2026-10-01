"""Pruebas unitarias de los lectores de correos del radar.

Usan textos de ejemplo INVENTADOS con la misma estructura que los correos
reales (sin datos personales ni links de seguimiento). Correr desde
services/profile-api con:  python3 -m pytest tests -v
"""
from app.parsers import (
    elegir_lector,
    parse_computrabajo,
    parse_indeed,
    parse_linkedin,
    parse_workana,
)

LINKEDIN = """Tu alerta de empleo para ("QA Analyst" OR "Software Tester")
AND
(Postman OR API)
NOT
(Senior) en Colombia
Nuevos empleos coinciden con tus preferencias.
Gestionar alertas: https://www.linkedin.com/comm/jobs/alerts?x=1

Analista QA Jr
Empresa Uno
Medellín
Ver anuncio de empleo: https://www.linkedin.com/comm/jobs/view/1111111111/?trackingId=abc&trk=x

---------------------------------------------------------

- QA Automation Tester
Empresa Dos
Colombia

3 contactos
Esta empresa busca personal activamente
Solicitar con perfil y CV
Ver anuncio de empleo: https://www.linkedin.com/comm/jobs/view/2222222222/?trackingId=def

---------------------------------------------------------
Nuevos empleos de tus otras alertas
Empleos de<strong>«Tester»</strong> en Colombia
Tester Funcional
Empresa Tres
Bogotá
Ver anuncio de empleo: https://www.linkedin.com/comm/jobs/view/3333333333/?x=1

---------------------------------------------------------
QA Funcional
Empresa Cuatro
Bogotá

3 personas estudiaron en la misma institución educativa que tú
Ver anuncio de empleo: https://www.linkedin.com/comm/jobs/view/4444444444/?x=1

---------------------------------------------------------
Editar alerta https://www.linkedin.com/jobs/jam/manage/999?x=1
Analista QA Jr
Empresa Uno
Medellín
Ver anuncio de empleo: https://www.linkedin.com/comm/jobs/view/1111111111/?otro=2
"""

WORKANA = """
Hola, Andrea:
Tenemos proyectos que pueden interesarte.

    Automatizar reportes con n8n
    ----------------------------
    Necesitamos conectar Google Sheets con Telegram usando n8n.
    Presupuesto a convenir...
    Leer más: https://www.workana.com/job/automatizar-reportes-con-n8n?ref=email_digest

    Pruebas manuales de app móvil
    -----------------------------
    Buscamos tester para una app de delivery.
    Leer más: https://www.workana.com/job/pruebas-manuales-de-app-movil

Puedes revisar este y otros proyectos haciendo clic en el siguiente link:
https://www.workana.com/jobs
"""

COMPUTRABAJO_RESUMEN = """Andrea!Tenemos 7 vacantes que se ajustan a tu perfil técnico y seniority.
Tester sénior
Revisa las vacantes
[https://go.computrabajo.com/go/app/o_grid?url=x]
"""


def test_linkedin_saca_titulo_empresa_ubicacion():
    ofertas = parse_linkedin(LINKEDIN)
    assert [o["title"] for o in ofertas] == [
        "Analista QA Jr",
        "QA Automation Tester",  # se quita el "- " inicial
        "Tester Funcional",
        "QA Funcional",
    ]
    assert ofertas[0]["company"] == "Empresa Uno"
    assert ofertas[0]["location"] == "Medellín"
    assert ofertas[2]["company"] == "Empresa Tres"


def test_linkedin_ignora_encabezados_y_ruido():
    titulos = [o["title"] for o in parse_linkedin(LINKEDIN)]
    for ruido in ("AND", "Esta empresa busca personal activamente", "3 contactos"):
        assert ruido not in titulos


def test_linkedin_link_limpio_y_sin_repetidos():
    ofertas = parse_linkedin(LINKEDIN)
    # 1111111111 aparece dos veces en el correo pero se devuelve una sola vez
    assert [o["external_id"] for o in ofertas] == [
        "1111111111", "2222222222", "3333333333", "4444444444"
    ]
    assert ofertas[0]["url"] == "https://www.linkedin.com/jobs/view/1111111111/"
    assert all(o["tipo"] == "empleo" and o["source"] == "linkedin" for o in ofertas)


def test_workana_saca_proyectos_freelance():
    proyectos = parse_workana(WORKANA)
    assert [p["title"] for p in proyectos] == [
        "Automatizar reportes con n8n",
        "Pruebas manuales de app móvil",
    ]
    assert proyectos[0]["tipo"] == "freelance"
    assert proyectos[0]["url"] == "https://www.workana.com/job/automatizar-reportes-con-n8n"
    assert "Google Sheets" in proyectos[0]["description"]


def test_computrabajo_resumen_no_trae_vacantes():
    assert parse_computrabajo(COMPUTRABAJO_RESUMEN) == []


def test_correo_vacio_no_rompe():
    assert parse_linkedin("") == []
    assert parse_workana("") == []


def test_elegir_lector_por_remitente():
    assert elegir_lector("jobalerts-noreply@linkedin.com")[0] == "linkedin"
    assert elegir_lector("notification@notifications.workana.com")[0] == "workana"
    assert elegir_lector("empleos_co@computrabajo.com")[0] == "computrabajo"
    assert elegir_lector("alguien@banco.com") == (None, None)


def test_linkedin_ignora_personas_de_tu_institucion():
    """Regresión 2026-09-30: la línea "N personas estudiaron en la misma
    institución..." corría los campos (título = empresa, empresa = ciudad)."""
    qa = [o for o in parse_linkedin(LINKEDIN) if o["external_id"] == "4444444444"][0]
    assert (qa["title"], qa["company"], qa["location"]) == ("QA Funcional", "Empresa Cuatro", "Bogotá")


INDEED = """Indeed Job Alert
3 puestos disponibles de tester en remoto

Jobs 1-3 of 3 new jobs
See matching results on Indeed: https://co.indeed.com/jobs?q=tester&l=remoto&from=ja

Tester Manual Jr
Empresa Alfa - Desde casa
Buscamos tester para pruebas funcionales de una app web…
Recién publicado
https://co.indeed.com/rc/clk/dl?jk=aaaa1111bbbb2222&from=ja&qd=xyz&tk=1

QA Automation
Empresa Beta S.A.S.  - Medellín, Antioquia
$5.000.000 - $6.000.000 por mes
Postulación vía Indeed
Automatización con Python y pytest para servicios REST.
hace 3 días
https://co.indeed.com/rc/clk/dl?jk=cccc3333dddd4444&from=ja

Analista de Pruebas
Empresa Gamma - Norte - Bogotá, Cundinamarca
Esta empresa responde a los candidatos
Pruebas de regresión y reporte de bugs en Jira.
hace 1 día
https://co.indeed.com/rc/clk/dl?jk=eeee5555ffff6666&from=ja

No compartas este email
En este email, se incluyen enlaces seguros personalizados para ti.

Administrar alertas de empleo: https://subscriptions.indeed.com?token=abc
"""


def test_indeed_saca_las_tres_vacantes():
    vacantes = parse_indeed(INDEED)
    assert [v["external_id"] for v in vacantes] == [
        "aaaa1111bbbb2222", "cccc3333dddd4444", "eeee5555ffff6666"]
    assert all(v["source"] == "indeed" and v["tipo"] == "empleo" for v in vacantes)


def test_indeed_separa_empresa_ubicacion_y_limpia_url():
    primera, segunda, tercera = parse_indeed(INDEED)
    assert primera["title"] == "Tester Manual Jr"
    assert primera["company"] == "Empresa Alfa"
    assert primera["location"] == "Remoto"
    assert primera["url"] == "https://co.indeed.com/viewjob?jk=aaaa1111bbbb2222"
    assert segunda["company"] == "Empresa Beta S.A.S."
    assert segunda["location"] == "Medellín, Antioquia"
    # Empresa con guion en el nombre: se corta en el ÚLTIMO " - ".
    assert tercera["company"] == "Empresa Gamma - Norte"
    assert tercera["location"] == "Bogotá, Cundinamarca"


def test_indeed_descripcion_sin_salario_ni_etiquetas():
    segunda = parse_indeed(INDEED)[1]
    assert segunda["description"] == "Automatización con Python y pytest para servicios REST."


def test_indeed_elegir_lector():
    assert elegir_lector("donotreply@jobalert.indeed.com")[0] == "indeed"
