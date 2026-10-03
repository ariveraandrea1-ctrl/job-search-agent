#!/bin/bash
# backup-db.sh
#
# Saca una copia (respaldo) de toda la base de datos Postgres del proyecto:
# vacantes, perfiles, CVs, respuestas de entrevista Y lo de n8n
# (workflows y credenciales, porque n8n guarda todo en la misma base).
#
# Deja dos archivos en database/backups/ (esa carpeta NO se sube a git):
#   job_search_agent_AAAA-MM-DD_HHMM.dump    -> el respaldo (formato de pg_dump)
#   job_search_agent_AAAA-MM-DD_HHMM.conteo  -> cuantas filas tenia cada tabla
#                                                (lo usa probar-restauracion.sh)
#
# Guarda solo los ultimos 14 respaldos; los mas viejos se borran solos.
#
# Uso:
#   bash scripts/backup-db.sh
#
# Ojo: las credenciales de n8n quedan cifradas con N8N_ENCRYPTION_KEY del .env.
# Para restaurarlas en otro lado hace falta esa misma clave.

set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose --env-file .env -f compose/docker-compose.local.yml"
CARPETA="database/backups"
GUARDAR=14
TABLAS="opportunities profiles documents interview_answers interview_questions conversation_state workflow_entity credentials_entity"

mkdir -p "$CARPETA"
FECHA=$(date +%Y-%m-%d_%H%M)
ARCHIVO="$CARPETA/job_search_agent_${FECHA}.dump"
CONTEO="$CARPETA/job_search_agent_${FECHA}.conteo"

echo "==> Contando filas de las tablas principales..."
: > "$CONTEO"
for t in $TABLAS; do
  n=$($COMPOSE exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -tA -c 'select count(*) from $t'")
  echo "$t $n" >> "$CONTEO"
done

echo "==> Sacando el respaldo..."
if ! $COMPOSE exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$ARCHIVO"; then
  echo "ERROR: fallo pg_dump. Borro el archivo incompleto."
  rm -f "$ARCHIVO" "$CONTEO"
  exit 1
fi

if [ ! -s "$ARCHIVO" ]; then
  echo "ERROR: el respaldo quedo vacio."
  rm -f "$ARCHIVO" "$CONTEO"
  exit 1
fi

echo "==> Borrando respaldos viejos (se guardan los ultimos $GUARDAR)..."
ls -1t "$CARPETA"/job_search_agent_*.dump 2>/dev/null | tail -n +$((GUARDAR + 1)) | while read -r viejo; do
  rm -f "$viejo" "${viejo%.dump}.conteo"
done

echo ""
echo "Listo. Respaldo: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"
echo "Filas por tabla:"
sed 's/^/  /' "$CONTEO"
