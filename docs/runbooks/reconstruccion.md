# Runbook: reconstrucción desde cero (Proyecto 1)

Uno de los puntos de la definición de terminado es poder reconstruir el sistema solo con el repositorio y el `.env.example`. Con este documento, el repo y las claves de cada servicio se puede levantar todo en un computador nuevo. Lo que no viaja en el repo, que son los secretos y los datos, se crea en los pasos 2 y 5.

## Lo que necesitas

- Docker Desktop (con Docker Compose v2) y Git.
- Python 3.10 o superior, para los scripts de `scripts/`.
- Un bot de Telegram (se crea con BotFather y el comando `/newbot`) y tu user id de Telegram.
- Claves de API de Groq y de Gemini (Google AI Studio).
- Opcional: una cuenta de Gmail con contraseña de aplicación y la etiqueta "Radar", si quieres el radar por correo (ver `docs/decisions/005`).

## 1. Clonar

```
git clone https://github.com/ariveraandrea1-ctrl/job-search-agent.git
cd job-search-agent
git checkout develop
```

## 2. Crear el .env

```
cp .env.example .env
```

Completa todos los `changeme`, además de `TELEGRAM_BOT_TOKEN`, `ADMIN_TELEGRAM_USER_ID`, `GROQ_API_KEY`, `GEMINI_API_KEY` y, si vas a usar el correo, `IMAP_USER` e `IMAP_PASSWORD`.

La `N8N_ENCRYPTION_KEY` se genera una sola vez con `openssl rand -hex 32` y hay que guardarla bien: sin ella no se pueden leer las credenciales de n8n ni restaurar un respaldo.

## 3. Levantar los servicios

```
bash scripts/start-local.sh
```

Esto levanta Postgres, MinIO, Mailpit, profile-api, n8n y el túnel de Cloudflare, y guarda en el `.env` la URL pública del túnel. Cuando profile-api arranca aplica todas las migraciones: las tablas, las preguntas de la entrevista, el tenant principal y la admin que pusiste en `ADMIN_TELEGRAM_USER_ID`. El bucket de MinIO se crea solo cuando llega el primer CV.

Para comprobar que profile-api está bien:

```
curl -s localhost:8000/health
```

## 4. Crear la cuenta de n8n

Abre http://localhost:5678 y crea la cuenta de dueña con correo y contraseña.

## 5. Importar flujos y credenciales

```
python3 scripts/importar-n8n.py
```

El script crea las 6 credenciales (Telegram, Postgres, Groq, Gemini, Gmail IMAP y SMTP/Mailpit) con los mismos ids que usan los flujos, e importa los 8 flujos. Las alertas de errores quedan dirigidas a `ADMIN_TELEGRAM_USER_ID`.

## 6. Publicar los flujos

En n8n abre cada flujo y dale Publish. Primero los subflujos, en este orden: `ai-model-router`, `verificar-acceso`, `alertas-errores`, `telegram-invitacion`, `radar-getonbrd`, `radar-puntaje`, `radar-resumen-diario` y, solo si configuraste Gmail, `radar-correo`.

En los Settings de cada flujo revisa que el Error workflow sea `alertas-errores`.

Antes de seguir, confirma que Telegram tiene registrada la URL del túnel (ver "Si el bot no responde después de arrancar" en `entorno-local.md`).

## 7. Probar

1. Escríbele `/start` al bot. Como la admin ya existe, debe responder "Ya tienes acceso".
2. Escribe `/subir_cv` y manda un CV en PDF o Word. El bot debe armar el perfil y hacer las preguntas que falten.
3. Escribe `/preferencias`. Deben aparecer palabras clave sugeridas a partir del CV.
4. Corre las pruebas automáticas contra el sistema real:
   ```
   python3 scripts/probar-aislamiento.py
   python3 scripts/probar-idempotencia.py
   ```
5. Prueba el respaldo y la restauración:
   ```
   bash scripts/backup-db.sh
   bash scripts/probar-restauracion.sh
   ```

## Probar la reconstrucción sin tocar tu instalación

Si quieres repetir esta prueba en el mismo computador donde ya corre el sistema:

0. Antes de empezar, ten a mano la contraseña de tu n8n. Las dos instalaciones usan la misma dirección (localhost:5678), así que al entrar al n8n de prueba el navegador reemplaza la sesión del original y después te la pide. Si no la recuerdas, saca un respaldo (`bash scripts/backup-db.sh`) y corre `docker compose --env-file .env -f compose/docker-compose.local.yml exec n8n n8n user-management:reset` seguido de un `restart n8n`. Eso borra solo los usuarios; los flujos, las credenciales y las ejecuciones se conservan, y puedes crear la cuenta otra vez.
1. Apaga la instalación actual sin borrar datos, es decir, sin `-v`, para que los volúmenes se conserven:
   ```
   docker compose --env-file .env -f compose/docker-compose.local.yml down
   ```
2. Clona el repo en otra carpeta. En el `.env` de esa copia usa `COMPOSE_PROJECT_NAME=jsa-reconstruccion` (así los volúmenes quedan aparte), otro bot de Telegram (un bot solo puede tener un webhook) y deja vacías las variables `IMAP_*`, para que la prueba no lea tus correos.
3. Sigue los pasos 3 a 7.
4. Cuando termines, borra la prueba con sus volúmenes, desde la carpeta de prueba:
   ```
   docker compose --env-file .env -f compose/docker-compose.local.yml down -v
   ```
5. Vuelve a la carpeta original y corre `bash scripts/start-local.sh`.

## Resultado de la prueba (2026-10-07)

Hice la reconstrucción completa en una carpeta nueva, solo con el repo y el `.env.example`. Se aplicaron las 15 migraciones, se creó la admin, `importar-n8n.py` importó 5 credenciales y 8 flujos, el bot de prueba respondió y Groq procesó un CV que quedó guardado en MinIO. Las pruebas automáticas dieron aislamiento 42/42 e idempotencia 15/15, y el respaldo con restauración recuperó las 8 tablas y MinIO.

Lo que encontré en el camino y corregí en el repo está en el BUG-31 de `docs/bitacora-bugs.md`.
