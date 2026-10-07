#!/usr/bin/env python3
"""importar-n8n.py — carga en un n8n VACÍO los workflows y credenciales del repo.

Es el paso de n8n de la reconstrucción desde cero (docs/runbooks/reconstruccion.md).
Las credenciales NO están en el repo (son secretos): este script las arma
con los valores del .env y las importa con los MISMOS ids que usan los
workflows exportados, así cada nodo queda conectado a su credencial sin
tener que elegirla a mano.

  1. Lee el .env.
  2. Arma credenciales: Telegram, Postgres, Groq, Gemini, Gmail (IMAP) y
     correo de salida (SMTP / Mailpit).
  3. Copia los workflows de n8n/workflows/ (cambiando el chat de alertas
     por ADMIN_TELEGRAM_USER_ID) y los importa con `n8n import:workflow`.
  4. Borra del contenedor el archivo temporal con las credenciales.

Uso (desde la raíz del repo, con los servicios arriba y la cuenta de dueña
de n8n ya creada en http://localhost:5678):
    python3 scripts/importar-n8n.py

Después: abrir cada workflow en n8n y darle Publish (ver el runbook).
Solo usa la librería estándar de Python.
"""
import json
import os
import subprocess
import sys
import tempfile

COMPOSE = ["docker", "compose", "--env-file", ".env", "-f", "compose/docker-compose.local.yml"]
CARPETA = "n8n/workflows"
# Workflows que no se importan (pruebas viejas).
OMITIR = {"test-conexion-postgres.json"}
# Chat id de la admin con el que se exportó alertas-errores; se reemplaza
# por el ADMIN_TELEGRAM_USER_ID del .env.
CHAT_ADMIN_EXPORTADO = "8553351572"


def leer_env(ruta: str = ".env") -> dict:
    valores = {}
    with open(ruta) as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                valores[clave.strip()] = valor.strip()
    return valores


def credenciales(env: dict) -> list[dict]:
    """Mismos id, nombre y tipo que en los workflows exportados."""
    def falta(*claves):
        return [c for c in claves if not env.get(c) or env[c].startswith("changeme")]

    faltan = falta("TELEGRAM_BOT_TOKEN", "POSTGRES_USER", "POSTGRES_PASSWORD",
                   "POSTGRES_DB", "GROQ_API_KEY", "GEMINI_API_KEY")
    if faltan:
        sys.exit("Faltan en .env: " + ", ".join(faltan))
    creds = [
        {"id": "aF0RvNa5kJZkarDY", "name": "Telegram account", "type": "telegramApi",
         "data": {"accessToken": env["TELEGRAM_BOT_TOKEN"]}},
        {"id": "EvPGGiXFOJMKZE5Q", "name": "Postgres account", "type": "postgres",
         "data": {"host": env.get("POSTGRES_HOST", "postgres"), "port": int(env.get("POSTGRES_PORT", 5432)),
                  "database": env["POSTGRES_DB"], "user": env["POSTGRES_USER"],
                  "password": env["POSTGRES_PASSWORD"], "ssl": "disable"}},
        {"id": "rOYFwrIeDiQSQE49", "name": "Groq account", "type": "groqApi",
         "data": {"apiKey": env["GROQ_API_KEY"]}},
        {"id": "IA9mniqBEqERvPFC", "name": "Google Gemini(PaLM) Api account", "type": "googlePalmApi",
         "data": {"host": "https://generativelanguage.googleapis.com", "apiKey": env["GEMINI_API_KEY"]}},
        {"id": "Zk3jNVFRs48PWLvE", "name": "Mailpit", "type": "smtp",
         "data": {"host": env.get("SMTP_HOST") or "mailpit", "port": int(env.get("SMTP_PORT") or 1025),
                  "user": env.get("SMTP_USER", ""), "password": env.get("SMTP_PASSWORD", ""),
                  "secure": False}},
    ]
    if env.get("IMAP_USER") and env.get("IMAP_PASSWORD"):
        creds.append({"id": "YOibyutjQjhMv6Uq", "name": "Gmail radar (IMAP)", "type": "imap",
                      "data": {"host": env.get("IMAP_HOST") or "imap.gmail.com",
                               "port": int(env.get("IMAP_PORT") or 993),
                               "user": env["IMAP_USER"], "password": env["IMAP_PASSWORD"],
                               "secure": True}})
    else:
        print("  (sin IMAP_USER/IMAP_PASSWORD: no se crea la credencial de Gmail; "
              "radar-correo quedará sin credencial)")
    return creds


def correr(*args: str) -> None:
    subprocess.run(COMPOSE + list(args), check=True, stdin=subprocess.DEVNULL)


def main() -> int:
    env = leer_env()
    admin = env.get("ADMIN_TELEGRAM_USER_ID", "")
    if not admin.isdigit():
        sys.exit("Falta ADMIN_TELEGRAM_USER_ID en .env (número de Telegram de la admin).")

    with tempfile.TemporaryDirectory() as tmp:
        carpeta_wf = os.path.join(tmp, "workflows")
        os.makedirs(carpeta_wf)
        nombres = []
        for nombre in sorted(os.listdir(CARPETA)):
            if not nombre.endswith(".json") or nombre in OMITIR:
                continue
            with open(os.path.join(CARPETA, nombre)) as f:
                texto = f.read()
            texto = texto.replace(f'"chatId": "{CHAT_ADMIN_EXPORTADO}"', f'"chatId": "{admin}"')
            with open(os.path.join(carpeta_wf, nombre), "w") as f:
                f.write(texto)
            nombres.append(nombre)
        with open(os.path.join(tmp, "credenciales.json"), "w") as f:
            json.dump(credenciales(env), f)

        print("==> Copiando al contenedor de n8n…")
        correr("exec", "-T", "-u", "root", "n8n", "rm", "-rf", "/tmp/importar")
        correr("cp", tmp, "n8n:/tmp/importar")
        # docker cp conserva los permisos del Mac (solo tu usuario puede leer);
        # n8n corre como el usuario "node" dentro del contenedor.
        correr("exec", "-T", "-u", "root", "n8n", "chown", "-R", "node:node", "/tmp/importar")
        try:
            print("==> Importando credenciales…")
            correr("exec", "-T", "n8n", "n8n", "import:credentials", "--input=/tmp/importar/credenciales.json")
            print(f"==> Importando {len(nombres)} workflows: {', '.join(nombres)}")
            correr("exec", "-T", "n8n", "n8n", "import:workflow", "--separate", "--input=/tmp/importar/workflows")
        finally:
            correr("exec", "-T", "-u", "root", "n8n", "rm", "-rf", "/tmp/importar")  # no dejar secretos en el contenedor
    print("\nListo. Abre http://localhost:5678, revisa que estén los workflows y dale Publish a cada uno "
          "(ver docs/runbooks/reconstruccion.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
