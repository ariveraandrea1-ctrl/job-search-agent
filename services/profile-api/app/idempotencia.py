"""Claves de idempotencia (especificación, sección 7.2).

"Toda ejecución usa idempotency_key" y "un reintento no crea una segunda
vacante o notificación". Las vacantes ya lo cumplen con dedup_key (restricción
única). Aquí están las claves de lo demás; se guardan en la tabla
idempotency_keys: si la clave ya estaba, es un reintento y no se repite.
"""
from datetime import datetime, timedelta, timezone

COLOMBIA = timezone(timedelta(hours=-5))  # Colombia no tiene horario de verano


def clave_update(update_id: int) -> str:
    """Un mensaje de Telegram (update_id) se atiende una sola vez."""
    return f"telegram-update:{int(update_id)}"


def clave_resumen(telegram_user_id: int, ahora: datetime) -> str:
    """Un resumen diario por usuario y por día (día de Colombia)."""
    return f"resumen:{int(telegram_user_id)}:{ahora.astimezone(COLOMBIA).date().isoformat()}"
