"""Usuarios e invitaciones (multiusuario, Semana 7).

Funciones puras (sin base de datos) para que se puedan probar con pytest:
- generar_codigo: código de invitación corto y fácil de copiar.
- leer_codigo_start: saca el código de "/start CODIGO".
- revisar_invitacion: dice si una invitación se puede usar y, si no, por qué.
- textos que el bot manda en cada caso.

Reglas:
- Solo la administradora (rol "admin") puede crear invitaciones (/invitar).
- Cada código sirve UNA vez y vence a los INVITACION_DIAS días.
- Quien no está registrado solo puede escribir /start CODIGO.
"""
import re
import secrets
from datetime import datetime, timedelta

# Sin letras/números que se confunden al copiar (0/O, 1/I/L).
ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LARGO_CODIGO = 8
INVITACION_DIAS = 7

_START = re.compile(r"^\s*/start(?:@\w+)?(?:\s+([A-Za-z0-9-]+))?\s*$")


def generar_codigo(largo: int = LARGO_CODIGO) -> str:
    """Código aleatorio (seguro, no adivinable) de `largo` caracteres."""
    return "".join(secrets.choice(ALFABETO) for _ in range(largo))


def leer_codigo_start(texto: str | None) -> str | None:
    """'/start ab12cd34' → 'AB12CD34'. Sin código o sin /start → None."""
    m = _START.match(texto or "")
    if not m or not m.group(1):
        return None
    return m.group(1).replace("-", "").upper()


def vence(creada: datetime, dias: int = INVITACION_DIAS) -> datetime:
    return creada + timedelta(days=dias)


def revisar_invitacion(invitacion: dict | None, ahora: datetime) -> str | None:
    """None si la invitación sirve; si no, el motivo: no_existe, usada, vencida."""
    if invitacion is None:
        return "no_existe"
    if invitacion.get("used_by") is not None:
        return "usada"
    if ahora >= invitacion["expires_at"]:
        return "vencida"
    return None


TEXTOS_RECHAZO = {
    "sin_codigo": ("👋 Hola. Este bot funciona solo por invitación.\n"
                   "Si alguien te invitó, escribe /start y el código que te dio. "
                   "Ejemplo: /start AB12CD34"),
    "no_existe": "❌ Ese código no existe. Revisa que lo hayas copiado completo.",
    "usada": "❌ Ese código ya fue usado. Pide una invitación nueva.",
    "vencida": "⌛ Ese código ya venció. Pide una invitación nueva.",
}

TEXTO_BIENVENIDA = (
    "🎉 ¡Listo, ya tienes acceso!\n\n"
    "Primer paso: envíame tu hoja de vida en PDF o Word. La leo, armo tu "
    "perfil y te hago unas preguntas cortas para completarlo.\n\n"
    "Después te iré avisando de vacantes que encajan contigo."
)

TEXTO_YA_REGISTRADO = "👋 Ya estás registrada/o. Escribe /perfil para ver tu perfil o envíame tu CV."

TEXTO_NO_ADMIN = "Solo la administradora puede crear invitaciones."


def texto_invitacion(codigo: str, expira: datetime) -> str:
    return (f"🎟 Invitación creada: {codigo}\n\n"
            f"Pásale este mensaje a la persona:\n"
            f"\"Abre el bot y escribe: /start {codigo}\"\n\n"
            f"Sirve una sola vez y vence el {expira.strftime('%d/%m/%Y')}.")


def avisa_radar(estado: str | None, creadas: int) -> bool:
    """Si el radar debe avisar por Telegram de las vacantes nuevas.

    Solo avisa si hay vacantes nuevas y el usuario no está en pausa. Las
    vacantes se guardan igual; lo único que se frena es el aviso (BUG-34).
    """
    return creadas > 0 and estado != "pausado"
