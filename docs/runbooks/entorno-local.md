# Runbook: entorno local (Proyecto 1)

## Levantar todo

Usar siempre el script, que ya hace lo necesario (incluye el `--env-file`
correcto y renueva el túnel de Cloudflare):

```
bash scripts/start-local.sh
```

Si necesitás correr `docker compose` a mano (por ejemplo para un servicio
puntual), el comando base, siempre desde la raíz del repo, es:

```
docker compose --env-file .env -f compose/docker-compose.local.yml <comando>
```

**No omitir `--env-file .env`.** Sin él, docker compose no encuentra los
valores de `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, etc. (el
`.env` vive en la raíz del repo, no en `compose/`), y los interpola como
cadenas vacías. Eso hace que, si algún servicio necesita recrearse,
`postgres` y `minio` se recreen con esas variables en blanco. No se pierden
datos (los volúmenes `postgres_data`/`minio_data` son nombrados y
persisten), pero es un riesgo innecesario y puede dejar `profile-api` sin
poder conectarse a la base.

## Cambiar código de `profile-api`

El servicio se construye con `COPY app ./app` en el build (sin bind mount),
así que un cambio en `services/profile-api/app/*.py` no se ve hasta
reconstruir la imagen:

```
docker compose --env-file .env -f compose/docker-compose.local.yml build profile-api
docker compose --env-file .env -f compose/docker-compose.local.yml up -d profile-api
```

Verificar que arrancó bien:

```
docker compose --env-file .env -f compose/docker-compose.local.yml logs profile-api --tail 40
```

## Agregar una tabla nueva (migraciones)

`profile-api` usa Alembic, con migraciones escritas **a mano** en
`services/profile-api/migrations/versions/000N_descripcion.py`, numeradas
secuencialmente (`0001`, `0002`, ...), no con ids autogenerados tipo hash.

**Por qué a mano y no `alembic revision --autogenerate`:** Postgres es
compartido entre `profile-api` y n8n (misma base, mismo esquema `public`).
`--autogenerate` compara los modelos de `app/models.py` contra TODAS las
tablas que existen en la base, así que además de detectar la tabla nueva
también "detecta" que le faltan al modelo todas las tablas internas de
n8n (`workflow_entity`, `credentials_entity`, `execution_entity`, etc.) y
genera un `op.drop_table(...)` para cada una. Si ese archivo se aplica tal
cual con `alembic upgrade head`, borra el n8n del usuario por completo.

Procedimiento seguro:

1. Agregar la clase nueva en `app/models.py` (mismo estilo que `Document`:
   `Mapped` / `mapped_column`, `id` UUID con `default=uuid.uuid4`).
2. Escribir a mano `migrations/versions/000N_descripcion.py`, con
   `revision = "000N"`, `down_revision = "<N-1 con padding>"`, y solo
   `op.create_table(...)` / `op.create_index(...)` para la tabla nueva
   (copiar la estructura de `0001_create_documents_table.py`).
3. (Opcional, para revisar antes de aplicar) generar con autogenerate en un
   archivo aparte solo para inspeccionar qué detecta, pero nunca aplicarlo
   tal cual ni dejarlo en `migrations/versions/`.
4. Reconstruir y levantar `profile-api` (paso anterior) para que la imagen
   incluya la migración nueva.
5. Aplicar: `docker compose --env-file .env -f compose/docker-compose.local.yml exec profile-api alembic upgrade head`
6. Verificar que las tablas de n8n siguen ahí, por ejemplo:
   ```
   docker compose --env-file .env -f compose/docker-compose.local.yml exec postgres \
     sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -c \"select count(*) from information_schema.tables where table_name in ('workflow_entity','credentials_entity','execution_entity');\""
   ```
   Debería devolver `3`.

## Historial

- 2026-09-23: agregada `interview_answers` (migración `0002`) siguiendo este
  procedimiento, después de que un `--autogenerate` sin revisar generó DROP
  de todas las tablas de n8n (no se llegó a aplicar).
