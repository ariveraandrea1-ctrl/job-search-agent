from datetime import datetime, timezone

from app import idempotencia as i


def test_clave_update():
    assert i.clave_update(123) == "telegram-update:123"
    assert i.clave_update(123) == i.clave_update("123")  # misma clave → reintento


def test_clave_resumen_usa_el_dia_de_colombia():
    # 2 am UTC del 7 de octubre = 9 pm del 6 de octubre en Colombia
    ahora = datetime(2026, 10, 7, 2, 0, tzinfo=timezone.utc)
    assert i.clave_resumen(55, ahora) == "resumen:55:2026-10-06"


def test_clave_resumen_cambia_de_un_dia_a_otro():
    a = datetime(2026, 10, 6, 16, 0, tzinfo=timezone.utc)
    b = datetime(2026, 10, 7, 16, 0, tzinfo=timezone.utc)
    assert i.clave_resumen(55, a) != i.clave_resumen(55, b)
    assert i.clave_resumen(55, a) != i.clave_resumen(56, a)
