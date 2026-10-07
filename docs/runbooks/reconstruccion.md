# Runbook: reconstrucción desde cero (Proyecto 1)

Definición de terminado: *"Reconstrucción desde repositorio y .env.example"*.
Con este documento, el repo y las claves de cada servicio se levanta el
sistema completo en un computador nuevo. Lo que **no** viaja en el repo
(secretos y datos) se crea en los pasos 2 y 5.

## Requisitos
- Docker Desktop (con Docker Compose v2) y Git.
- Python 3.10+ (para los scripts de `scripts/`).
- Un bot de Telegram (BotFather → `/newbot`) y tu user id de Telegram.
- Claves de API de Groq y de Gemini (Google AI Studio).
- Opcional: Gmail con contraseña de aplicación y la etiqueta "Radar" (radar
  por correo, ver `docs/decisions/005`).

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
Completar todos los `changeme`, `TELEGRAM_BOT_TOKEN`, `ADMIN_TELEGRAM_USER_ID`,
`GROQ_API_KEY`, `GEMINI_API_KEY` y (opcional) `IMAP_USER` / `IMAP_PASSWORD`.
`N8N_ENCRYPTION_KEY`: generar una vez con `openssl rand -hex 32` y guardarla
(sin ella no se pueden leer las credenciales ni restaurar respaldos).

## 3. Levantar los servicios
```
bash scripts/start-local.sh
```
Levanta Postgres, MinIO, Mailpit, profile-api, n8n y el túnel de Cloudflare,
y deja en el .env la URL pública del túnel. Al arrancar, profile-api aplica
**todas las migraciones** (tablas, preguntas de la entrevista, tenant
principal y la admin de `ADMIN_TELEGRAM_USER_ID`). El bucket de MinIO se
crea solo con el primer CV.

Verificar:
```
curl -s localhost:8000/health
```

## 4. Crear la cuenta de n8n
Abrir http://localhost:5678 y crear la cuenta de dueña (correo y contraseña).

## 5. Importar workflows y credenciales
```
python3 scripts/importar-n8n.py
```
Crea las 6 credenciales (Telegram, Postgres, Groq, Gemini, Gmail IMAP y
SMTP/Mailpit) con los mismos ids que usan los workflows, e importa los 8
workflows. Las alertas de errores quedan dirigidas a `ADMIN_TELEGRAM_USER_ID`.

## 6. Publicar los workflows
En n8n, abrir cada uno y darle **Publish**, en este orden (los subflujos
primero): `ai-model-router`, `verificar-acceso`, `alertas-errores`,
`telegram-invitacion`, `radar-getonbrd`, `radar-puntaje`,
`radar-resumen-diario` y `radar-correo` (solo si configuraste Gmail).
Revisar en Settings de cada uno que el **Error workflow** sea
`alertas-errores`.

## 7. Probar
1. Escribirle `/start` al bot → "Ya tienes acceso" (la admin ya existe).
2. `/subir_cv` y mandar un CV en PDF o Word → perfil + preguntas.
3. `/preferencias` → palabras sugeridas desde el CV.
4. Pruebas automáticas contra el sistema real:
   ```
   python3 scripts/probar-aislamiento.py
   python3 scripts/probar-idempotencia.py
   ```
5. Respaldo y restauración:
   ```
   bash scripts/backup-db.sh
   bash scripts/probar-restauracion.sh
   ```

## Probar la reconstrucción sin tocar tu instalación
Para repetir esta prueba en el mismo computador donde ya corre el sistema:
1. Apagar la instalación actual **sin borrar datos**:
   `docker compose --env-file .env -f compose/docker-compose.local.yml down`
   (sin `-v`; los volúmenes se conservan).
2. Clonar en otra carpeta y, en su `.env`, usar
   `COMPOSE_PROJECT_NAME=jsa-reconstruccion` (volúmenes aparte), **otro bot
   de Telegram** (un bot solo puede tener un webhook) y dejar `IMAP_*`
   vacío (para que la prueba no lea ni marque como leídos tus correos).
3. Seguir los pasos 3 a 7.
4. Borrar la prueba con sus volúmenes, desde la carpeta de prueba:
   `docker compose --env-file .env -f compose/docker-compose.local.yml down -v`
5. Volver a la carpeta original y `bash scripts/start-local.sh`.
