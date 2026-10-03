#!/bin/bash
# probar-restauracion.sh
#
# Prueba que un respaldo SIRVE: lo restaura en una base de datos aparte
# (job_search_agent_prueba_restauracion), cuenta las filas de cada tabla y
# las compara con las que tenia la base cuando se saco el respaldo
# (archivo .conteo). Al final borra esa base de prueba.
#
# NUNCA toca la base real.
#
# Uso:
#   bash scripts/probar-restauracion.sh                      # usa el respaldo mas reciente
#   bash scripts/probar-restauracion.sh database/backups/xxx.dump

set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose --env-file .env -f compose/docker-compose.local.yml"
PRUEBA="job_search_agent_prueba_restauracion"

ARCHIVO="${1:-$(ls -1t database/backups/job_search_agent_*.dump 2>/dev/null | head -1)}"
if [ -z "$ARCHIVO" ] || [ ! -f "$ARCHIVO" ]; then
  echo "ERROR: no encontre ningun respaldo. Corre primero: bash scripts/backup-db.sh"
  exit 1
fi
CONTEO="${ARCHIVO%.dump}.conteo"
if [ ! -f "$CONTEO" ]; then
  echo "ERROR: falta $CONTEO (el conteo de filas de ese respaldo)."
  exit 1
fi

psql_en() {  # psql_en <base> <sql>
  # < /dev/null: sin esto, docker se "come" el resto del archivo que lee el
  # while de abajo y solo se compara la primera tabla (BUG-17).
  $COMPOSE exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -d $1 -tA -v ON_ERROR_STOP=1 -c \"$2\"" < /dev/null
}

echo "==> Respaldo a probar: $ARCHIVO"
echo "==> Creando base de prueba $PRUEBA..."
psql_en postgres "drop database if exists $PRUEBA"
psql_en postgres "create database $PRUEBA"

echo "==> Restaurando..."
$COMPOSE exec -T postgres sh -c "pg_restore -U \"\$POSTGRES_USER\" -d $PRUEBA --no-owner --exit-on-error" < "$ARCHIVO"

echo "==> Comparando filas (esperado = al sacar el respaldo, obtenido = restaurado):"
FALLAS=0
REVISADAS=0
ESPERADAS=$(wc -l < "$CONTEO" | tr -d ' ')
printf "  %-22s %10s %10s\n" "tabla" "esperado" "obtenido"
while read -r tabla esperado; do
  obtenido=$(psql_en "$PRUEBA" "select count(*) from $tabla")
  marca="OK"
  if [ "$obtenido" != "$esperado" ]; then
    marca="DIFERENTE"
    FALLAS=$((FALLAS + 1))
  fi
  printf "  %-22s %10s %10s  %s\n" "$tabla" "$esperado" "$obtenido" "$marca"
  REVISADAS=$((REVISADAS + 1))
done < "$CONTEO"

if [ "$REVISADAS" -ne "$ESPERADAS" ]; then
  echo "  ERROR: solo se revisaron $REVISADAS de $ESPERADAS tablas."
  FALLAS=$((FALLAS + 1))
fi

echo "==> Borrando base de prueba..."
psql_en postgres "drop database $PRUEBA"

echo ""
if [ "$FALLAS" -eq 0 ]; then
  echo "PASO: el respaldo se restaura completo ($REVISADAS de $ESPERADAS tablas)."
else
  echo "FALLO: $FALLAS tabla(s) no coinciden. Puede pasar si n8n guardo algo justo"
  echo "mientras se sacaba el respaldo; saca otro y vuelve a probar."
  exit 1
fi
