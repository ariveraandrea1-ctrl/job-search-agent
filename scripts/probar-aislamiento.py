#!/usr/bin/env python3
"""probar-aislamiento.py — prueba automática de aislamiento con 5 usuarios.

Definición de terminado del Proyecto 1: "Cinco usuarios aislados pueden
registrarse". Este script lo demuestra contra el sistema REAL (profile-api
en localhost:8000 + Postgres en Docker):

  1. Registro: 5 usuarios de prueba (ids 900000101..105) se registran con
     invitaciones creadas por la admin; sin código no entran; un código no
     sirve dos veces; quien no es admin no puede invitar.
  2. Datos: cada uno guarda sus propias vacantes + una vacante COMPARTIDA
     (mismo link para los 5).
  3. Aislamiento: cada uno ve SOLO las suyas en /nuevas; nadie puede ver,
     guardar ni descartar una vacante de otro por su número; guardar la
     compartida no cambia la copia de los demás; cada uno tiene sus propias
     /preferencias; /pausar saca a uno del resumen sin afectar a los demás;
     cada resumen trae solo vacantes de su dueño.
  4. Limpieza: borra TODO lo que creó (antes y después), aunque falle.

Uso (desde la raíz del repo, con Docker y profile-api arriba):
    python3 scripts/probar-aislamiento.py

Solo usa la librería estándar de Python. Sale con código 1 si algo falla.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

BASE = os.environ.get("PROFILE_API", "http://localhost:8000")
USUARIOS = [900000101, 900000102, 900000103, 900000104, 900000105]
MARCA = "AISLAMIENTO-PRUEBA"
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


def comando(uid: int, texto: str) -> str:
    return api("POST", "/radar/comando", {"telegram_user_id": uid, "text": texto})["telegram_text"]


def esperar_api(segundos: int = 60) -> None:
    """Espera a que profile-api responda /health (recién reiniciado tarda unos segundos)."""
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
    ids = ", ".join(str(u) for u in USUARIOS)
    sql = (f"BEGIN; "
           f"DELETE FROM profiles WHERE telegram_user_id IN ({ids}); "
           f"DELETE FROM documents WHERE telegram_user_id IN ({ids}); "
           f"DELETE FROM interview_answers WHERE telegram_user_id IN ({ids}); "
           f"DELETE FROM conversation_state WHERE telegram_user_id IN ({ids}); "
           f"DELETE FROM opportunities WHERE telegram_user_id IN ({ids}); "
           f"DELETE FROM invitations WHERE used_by IN ({ids}); "
           f"DELETE FROM users WHERE telegram_user_id IN ({ids}); COMMIT;")
    subprocess.run(COMPOSE + ["exec", "-T", "postgres", "sh", "-c",
                              f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -c "{sql}"'],
                   check=True, stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL)


def main() -> int:
    admin = admin_id()
    print("==> Esperando a que profile-api esté listo…")
    esperar_api()
    print("==> Limpiando restos de corridas anteriores…")
    limpiar()
    numeros: dict[int, dict[str, int]] = {}
    try:
        print("\n1) Registro con invitación")
        r = api("POST", "/usuarios/acceso", {"telegram_user_id": USUARIOS[0], "text": "hola"})
        check(r["permitido"] is False and r["motivo"] == "sin_codigo", "Sin código no entra")
        codigos = []
        for uid in USUARIOS:
            inv = api("POST", "/usuarios/invitaciones", {"telegram_user_id": admin})
            r = api("POST", "/usuarios/acceso", {"telegram_user_id": uid, "text": f"/start {inv['code']}"})
            check(r["motivo"] == "registrado", f"Usuario {uid} se registra con su código")
            codigos.append(inv["code"])
        r = api("POST", "/usuarios/acceso", {"telegram_user_id": 900000199, "text": f"/start {codigos[0]}"})
        check(r["motivo"] == "usada", "Un código ya usado no sirve otra vez")
        r = api("POST", "/usuarios/invitaciones", {"telegram_user_id": USUARIOS[0]})
        check(r["ok"] is False, "Un usuario normal no puede crear invitaciones")
        for uid in USUARIOS:
            r = api("POST", "/usuarios/acceso", {"telegram_user_id": uid, "text": "/perfil"})
            check(r["permitido"] is True and r["rol"] == "usuario", f"Usuario {uid} ya registrado entra (rol usuario)")

        print("\n2) Cada usuario guarda sus vacantes (+ una compartida)")
        for i, uid in enumerate(USUARIOS, start=1):
            numeros[uid] = {}
            for letra in ("A", "B"):
                r = api("POST", "/opportunities", {
                    "telegram_user_id": uid, "tipo": "empleo", "source": "manual",
                    "title": f"{MARCA} U{i} vacante {letra}",
                    "url": f"https://example.com/{MARCA.lower()}/u{i}/{letra.lower()}"})
                numeros[uid][letra] = r["numero"]
            r = api("POST", "/opportunities", {
                "telegram_user_id": uid, "tipo": "empleo", "source": "manual",
                "title": f"{MARCA} compartida (copia de U{i})",
                "url": f"https://example.com/{MARCA.lower()}/compartida"})
            check(r["created"] is True, f"U{i}: la vacante compartida se guarda como copia propia")
            numeros[uid]["C"] = r["numero"]

        print("\n3) Aislamiento")
        for i, uid in enumerate(USUARIOS, start=1):
            texto = comando(uid, "/nuevas")
            propias = all(f"U{i} vacante {l}" in texto for l in ("A", "B"))
            ajenas = [j for j in range(1, 6) if j != i and f"U{j} vacante" in texto]
            check(propias and not ajenas, f"U{i}: /nuevas muestra solo sus vacantes")

        u1, u2 = USUARIOS[0], USUARIOS[1]
        ajeno = numeros[u2]["A"]
        check("No encontré" in comando(u1, f"/detalle {ajeno}"), "U1 no puede ver /detalle de una vacante de U2")
        check("No encontré" in comando(u1, f"/guardar {ajeno}"), "U1 no puede /guardar una vacante de U2")
        check("No encontré" in comando(u1, f"/descartar {ajeno}"), "U1 no puede /descartar una vacante de U2")
        check("U2 vacante A" in comando(u2, "/nuevas"), "La vacante de U2 sigue nueva para U2")

        comando(u1, f"/guardar {numeros[u1]['C']}")
        check("compartida" in comando(u1, "/guardadas"), "U1 guarda su copia de la compartida")
        check("compartida" in comando(u2, "/nuevas"), "La copia de U2 sigue nueva (estados independientes)")
        check("compartida" not in comando(u2, "/guardadas"), "U2 no ve como guardada la de U1")

        for i, uid in enumerate(USUARIOS, start=1):
            api("POST", "/usuarios/preferencias", {"telegram_user_id": uid, "text": f"/preferencias palabra{i}, tema{i}"})
        for i, uid in enumerate(USUARIOS, start=1):
            r = api("POST", "/usuarios/preferencias", {"telegram_user_id": uid, "text": "/preferencias"})
            check(r["palabras"] == [f"palabra{i}", f"tema{i}"], f"U{i}: /preferencias muestra solo las suyas")

        u3 = USUARIOS[2]
        comando(u3, "/pausar")
        ids_resumen = {it["telegram_user_id"] for it in api("GET", "/radar/resumenes")["items"]}
        check(u3 not in ids_resumen and {u1, u2} <= ids_resumen, "U3 pausado no recibe resumen; los demás sí")
        comando(u3, "/reanudar")
        items = {it["telegram_user_id"]: it["telegram_text"] for it in api("GET", "/radar/resumenes")["items"]}
        check(u3 in items, "U3 vuelve al resumen con /reanudar")
        for i, uid in enumerate(USUARIOS, start=1):
            texto = items.get(uid, "")
            ajenas = [j for j in range(1, 6) if j != i and f"U{j} vacante" in texto]
            check(not ajenas, f"U{i}: su resumen no trae vacantes de otros")
    finally:
        print("\n==> Limpiando datos de prueba…")
        limpiar()

    fallas = [d for ok, d in resultados if not ok]
    print(f"\nResultado: {len(resultados) - len(fallas)} de {len(resultados)} casos pasaron.")
    if fallas:
        print("FALLARON:\n  - " + "\n  - ".join(fallas))
        return 1
    print("PASO: los 5 usuarios están aislados.")
    return 0


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    sys.exit(main())
