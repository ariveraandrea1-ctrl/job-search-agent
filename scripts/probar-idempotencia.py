#!/usr/bin/env python3
"""probar-idempotencia.py — prueba automática de "fallos recuperables sin duplicados".

Definición de terminado del Proyecto 1 y especificación 7.2: "un reintento
no crea una segunda vacante o notificación" y "los callbacks de Telegram se
consumen una vez". Este script REPITE a propósito cada paso, como lo haría
un reintento después de una falla, contra el sistema REAL (profile-api en
localhost:8000 + Postgres en Docker), y revisa que no quede nada duplicado:

  1. Telegram reenvía un mensaje (mismo update_id): se atiende una sola vez.
     Incluye el /start con invitación: el reenvío NO responde "código usado".
  2. El radar se vuelve a correr con las mismas vacantes: 0 nuevas, 0 avisos.
  3. Se guarda dos veces la misma vacante: queda una sola.
  4. Se reintenta guardar el puntaje: una sola vacante, mismo puntaje.
  5. El resumen diario se vuelve a correr el mismo día: no sale repetido.
  6. Limpieza: borra todo lo que creó (antes y después), aunque falle.

Uso (desde la raíz del repo, con Docker y profile-api arriba):
    python3 scripts/probar-idempotencia.py

Solo usa la librería estándar de Python. Sale con código 1 si algo falla.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

BASE = os.environ.get("PROFILE_API", "http://localhost:8000")
USUARIO = 900000201
UPDATES = [990000001, 990000002]  # update_id falsos (Telegram usa otros rangos)
COMPOSE = ["docker", "compose", "--env-file", ".env", "-f", "compose/docker-compose.local.yml"]

resultados: list[tuple[bool, str]] = []


def check(ok: bool, descripcion: str) -> None:
    resultados.append((bool(ok), descripcion))
    print(("  ✅ " if ok else "  ❌ ") + descripcion)


def api(metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def sql(consulta: str) -> str:
    salida = subprocess.run(COMPOSE + ["exec", "-T", "postgres", "sh", "-c",
                                       f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -q -c "{consulta}"'],
                            check=True, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return salida.stdout.strip()


def esperar_api(segundos: int = 60) -> None:
    """Espera a que profile-api responda /health (BUG-25)."""
    limite = time.time() + segundos
    while time.time() < limite:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=3) as r:
                if r.status == 200:
                    return
        except OSError:
            pass
        time.sleep(2)
    sys.exit(f"profile-api no respondió en {segundos} s. ¿Está arriba el contenedor?")


def admin_id() -> int:
    with open(".env") as f:
        for linea in f:
            if linea.startswith("ADMIN_TELEGRAM_USER_ID="):
                return int(linea.split("=", 1)[1].strip())
    sys.exit("Falta ADMIN_TELEGRAM_USER_ID en .env")


def limpiar() -> None:
    u = USUARIO
    updates = " OR ".join(f"clave = 'telegram-update:{x}'" for x in UPDATES)
    sql(f"BEGIN; "
        f"DELETE FROM ai_calls WHERE telegram_user_id = {u}; "
        f"DELETE FROM opportunities WHERE telegram_user_id = {u}; "
        f"DELETE FROM idempotency_keys WHERE {updates} OR clave LIKE 'resumen:{u}:%'; "
        f"DELETE FROM invitations WHERE used_by = {u}; "
        f"DELETE FROM users WHERE telegram_user_id = {u}; COMMIT;")


def main() -> int:
    admin = admin_id()
    print("==> Esperando a que profile-api esté listo…")
    esperar_api()
    print("==> Limpiando restos de corridas anteriores…")
    limpiar()
    try:
        print("\n1) Telegram reenvía el mismo mensaje (mismo update_id)")
        inv = api("POST", "/usuarios/invitaciones", {"telegram_user_id": admin})
        inicio = {"telegram_user_id": USUARIO, "text": f"/start {inv['code']}", "update_id": UPDATES[0]}
        r = api("POST", "/usuarios/acceso", inicio)
        check(r["motivo"] == "registrado", "El /start con invitación registra al usuario")
        r = api("POST", "/usuarios/acceso", inicio)
        check(r.get("repetido") is True and "telegram_text" not in r,
              "El reenvío del /start se ignora (no responde 'código ya usado')")
        check(sql(f"SELECT count(*) FROM users WHERE telegram_user_id = {USUARIO}") == "1",
              "Hay un solo usuario registrado")
        msg = {"telegram_user_id": USUARIO, "text": "/nuevas", "update_id": UPDATES[1]}
        r = api("POST", "/usuarios/acceso", msg)
        check(r["permitido"] is True, "Un mensaje nuevo se atiende")
        r = api("POST", "/usuarios/acceso", msg)
        check(r.get("repetido") is True and r["permitido"] is False, "El mismo mensaje reenviado se ignora")
        r = api("POST", "/usuarios/acceso", {"telegram_user_id": USUARIO, "text": "/nuevas"})
        check(r["permitido"] is True, "Sin update_id (llamadas viejas) sigue funcionando")

        print("\n2) El radar se vuelve a correr con las mismas vacantes")
        ahora = int(time.time())
        respuesta = {"data": [{"id": "idem-prueba-qa-1", "attributes": {
            "title": "QA Tester Junior (prueba idempotencia)", "published_at": ahora,
            "remote_modality": "fully_remote", "countries": ["Remote"], "lang": "es"}}]}
        r1 = api("POST", "/radar/getonbrd", {"telegram_user_id": USUARIO, "response": respuesta})
        check(r1["created"] == 1, "Primera corrida: 1 vacante nueva")
        r2 = api("POST", "/radar/getonbrd", {"telegram_user_id": USUARIO, "response": respuesta})
        check(r2["created"] == 0 and r2["duplicates"] == 1 and not r2["new_items"],
              "Reintento: 0 nuevas, 1 duplicada, nada que avisar")
        check(sql(f"SELECT count(*) FROM opportunities WHERE telegram_user_id = {USUARIO} "
                  f"AND external_id = 'idem-prueba-qa-1'") == "1", "En la base hay una sola")

        print("\n3) Se guarda dos veces la misma vacante (/opportunities)")
        vacante = {"telegram_user_id": USUARIO, "tipo": "empleo", "source": "manual",
                   "title": "Analista de Pruebas (prueba idempotencia)",
                   "url": "https://ejemplo.com/idempotencia/1?utm_source=a"}
        a = api("POST", "/opportunities", vacante)
        b = api("POST", "/opportunities", {**vacante, "url": "https://ejemplo.com/idempotencia/1?utm_source=b"})
        check(a["created"] is True and b["created"] is False and a["id"] == b["id"],
              "El segundo intento devuelve la misma vacante (created = false)")

        print("\n4) Se reintenta guardar el puntaje de la IA")
        analisis = json.dumps({"puntaje": 72, "ingles": "desconocido", "nivel_vacante": "junior",
                               "razones_a_favor": ["Pide QA junior"], "razones_en_contra": [],
                               "senales_alerta": [], "resumen": "Prueba de idempotencia"})
        cuerpo = {"text": analisis, "provider": "groq", "prompt_version": "puntaje-v1"}
        s1 = api("POST", f"/opportunities/{a['id']}/score", cuerpo)
        s2 = api("POST", f"/opportunities/{a['id']}/score", cuerpo)
        check(s1["score"] == s2["score"], "Mismo puntaje en los dos intentos")
        check(sql(f"SELECT count(*) FROM opportunities WHERE telegram_user_id = {USUARIO}") == "2",
              "Siguen siendo 2 vacantes (el reintento no crea otra)")

        print("\n5) El resumen diario se vuelve a correr el mismo día")
        ruta = f"/radar/resumenes?telegram_user_id={USUARIO}"
        r = api("GET", ruta)
        check(r["count"] == 1, "Sin registrar (curl de prueba) sale y no marca nada")
        r = api("GET", ruta + "&registrar=true")
        check(r["count"] == 1, "Primera corrida del día: sale el resumen")
        r = api("GET", ruta + "&registrar=true")
        check(r["count"] == 0 and r["ya_enviados_hoy"] == 1 and not r["con_correo"],
              "Segunda corrida el mismo día: no sale repetido (ni Telegram ni correo)")
    finally:
        print("\n==> Limpiando lo que creó la prueba…")
        limpiar()

    fallas = [d for ok, d in resultados if not ok]
    print(f"\nResultado: {len(resultados) - len(fallas)}/{len(resultados)} casos OK")
    if fallas:
        print("FALLÓ:")
        for d in fallas:
            print("  - " + d)
        return 1
    print("PASÓ: los reintentos no crean duplicados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
