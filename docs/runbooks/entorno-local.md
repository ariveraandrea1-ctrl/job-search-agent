# Runbook: entorno local (Proyecto 1)

## Levantar todo

Siempre arranco con el script, porque ya pasa el `--env-file` correcto y renueva el túnel de Cloudflare:

```
bash scripts/start-local.sh
```

Si necesitas correr `docker compose` a mano, por ejemplo para un solo servicio, el comando base es este, siempre desde la raíz del repo:

```
docker compose --env-file .env -f compose/docker-compose.local.yml <comando>
```

No olvides el `--env-file .env`. El `.env` está en la raíz del repo y no en `compose/`, así que sin esa opción docker compose no encuentra `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` y las demás variables, y las deja vacías. Si en ese momento algún servicio se tiene que recrear, `postgres` y `minio` arrancan con esos valores en blanco. Los datos no se pierden, porque los volúmenes `postgres_data` y `minio_data` tienen nombre y se conservan, pero `profile-api` puede quedarse sin poder conectarse a la base.

## Si el bot no responde después de arrancar

Me pasó el 10 de octubre (BUG-36): el script terminó diciendo "Listo", los avisos de vacantes seguían llegando, pero el bot no respondía a ningún comando. Lo que sale del sistema funcionaba; lo que entra, no.

La razón es que Telegram manda los mensajes a la URL pública del túnel. Cada vez que el túnel se recrea, n8n tiene que avisarle a Telegram la URL nueva, y a veces ese aviso falla porque el túnel todavía no está listo.

Desde esa fecha `start-local.sh` lo revisa solo: espera a que el túnel responda, reinicia n8n y confirma con Telegram que quedó la URL nueva. Si no lo logra, termina con un aviso de "ATENCIÓN: el bot NO va a recibir mensajes" en vez de "Listo". Si ves ese aviso, o si el bot deja de responder con el sistema ya andando, sigue estos pasos.

Para revisarlo, le pregunto a Telegram qué URL tiene registrada (el comando lee el token del `.env` sin mostrarlo):

```
source <(grep TELEGRAM_BOT_TOKEN .env) && curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" | python3 -m json.tool
```

Si `url` sale vacía o con una dirección vieja:

1. Compruebo que el túnel ya responde. Tiene que dar `200`:
   ```
   curl -s -o /dev/null -w "%{http_code}\n" https://<url-del-tunel>/healthz
   ```
   La URL actual está en `WEBHOOK_URL` dentro del `.env`.
2. En n8n abro el flujo `telegram-invitacion`, lo desactivo y lo vuelvo a activar. Eso obliga a n8n a registrar el webhook otra vez.
3. Corro de nuevo `getWebhookInfo` y confirmo que `url` empieza por la dirección del túnel nuevo.

Los mensajes que se mandaron mientras el webhook estaba vacío se pierden, así que hay que volver a escribirlos.

## Cambiar código de `profile-api`

La imagen copia el código al construirse (`COPY app ./app`) y no usa un volumen compartido, así que un cambio en `services/profile-api/app/*.py` no se ve hasta reconstruirla:

```
docker compose --env-file .env -f compose/docker-compose.local.yml build profile-api
docker compose --env-file .env -f compose/docker-compose.local.yml up -d profile-api
```

Para revisar que arrancó bien:

```
docker compose --env-file .env -f compose/docker-compose.local.yml logs profile-api --tail 40
```

## Agregar una tabla nueva (migraciones)

`profile-api` usa Alembic. Las migraciones las escribo a mano en `services/profile-api/migrations/versions/000N_descripcion.py`, numeradas en orden (`0001`, `0002`, ...), y no con los ids automáticos de Alembic.

La razón para no usar `alembic revision --autogenerate` es que Postgres lo comparten `profile-api` y n8n: misma base y mismo esquema `public`. El autogenerate compara los modelos de `app/models.py` con todas las tablas que existen, así que además de la tabla nueva ve que en el modelo "faltan" las tablas internas de n8n (`workflow_entity`, `credentials_entity`, `execution_entity` y otras) y escribe un `op.drop_table(...)` para cada una. Si ese archivo se aplica sin revisarlo, borra n8n completo.

Así lo hago para no correr ese riesgo:

1. Agrego la clase nueva en `app/models.py`, con el mismo estilo de `Document`: `Mapped` y `mapped_column`, y el `id` como UUID con `default=uuid.uuid4`.
2. Escribo a mano `migrations/versions/000N_descripcion.py`, con `revision = "000N"`, `down_revision` igual al número anterior con ceros a la izquierda, y solo `op.create_table(...)` y `op.create_index(...)` para la tabla nueva. Sirve copiar la estructura de `0001_create_documents_table.py`.
3. Si quiero comparar, puedo correr el autogenerate en un archivo aparte solo para mirar qué detecta. Ese archivo nunca se aplica ni se deja en `migrations/versions/`.
4. Reconstruyo y levanto `profile-api` (sección anterior) para que la imagen tenga la migración nueva.
5. Aplico la migración:
   ```
   docker compose --env-file .env -f compose/docker-compose.local.yml exec profile-api alembic upgrade head
   ```
6. Reviso que las tablas de n8n siguen ahí:
   ```
   docker compose --env-file .env -f compose/docker-compose.local.yml exec postgres \
     sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"select count(*) from information_schema.tables where table_name in ('workflow_entity','credentials_entity','execution_entity');\""
   ```
   Tiene que devolver `3`.

## Historial

- 2026-09-23: agregué `interview_answers` (migración `0002`) con este procedimiento. Antes un `--autogenerate` sin revisar había generado el borrado de todas las tablas de n8n; por suerte no llegué a aplicarlo.
- 2026-10-10: agregué la sección "Si el bot no responde después de arrancar" (BUG-36).
- 2026-10-10: `start-local.sh` ahora verifica el webhook de Telegram al arrancar (corrección del BUG-36).
