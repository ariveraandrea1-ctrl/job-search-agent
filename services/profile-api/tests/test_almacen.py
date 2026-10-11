"""Pruebas de las funciones puras del almacén de archivos (app/almacen.py)."""
from app.almacen import clave_cv, huella, nombre_seguro


def test_huella_es_sha256_y_cambia_si_cambia_un_byte():
    assert huella(b"hola") == "b221d9dbb083a7f33428d7c2a3c3198ae925614d70210e28716ccaa7cd4ddb79"
    assert huella(b"hola") != huella(b"hola ")


def test_nombre_seguro_quita_tildes_espacios_y_simbolos():
    assert nombre_seguro("Mi CV (Andrea Rivera) – versión final.PDF") == "mi-cv-andrea-rivera-version-final.pdf"


def test_nombre_seguro_sin_nombre_o_sin_extension():
    assert nombre_seguro(None) == "archivo"
    assert nombre_seguro("cv") == "cv"


def test_clave_cv_sigue_la_estructura_de_la_especificacion():
    clave = clave_cv("00000000-0000-0000-0000-000000000001", 123, "CV final.pdf", "a" * 64)
    assert clave == ("tenants/00000000-0000-0000-0000-000000000001/users/123/"
                     "cv/original/aaaaaaaaaaaaaaaa-cv-final.pdf")


def test_huella_total_no_depende_del_orden_y_detecta_cambios():
    from app.respaldo_minio import huella_total
    a = [("x.pdf", "1"), ("y.pdf", "2")]
    assert huella_total(a) == huella_total(list(reversed(a)))
    assert huella_total(a) != huella_total([("x.pdf", "1"), ("y.pdf", "3")])
