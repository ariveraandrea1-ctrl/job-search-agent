#!/bin/bash
# start-local.sh
#
# Levanta todo el entorno local (n8n, postgres, minio, mailpit, profile-api,
# cloudflared) y renueva automaticamente el tunel de Cloudflare, que expira
# cada vez que se apaga el Mac o se reinicia Docker.
#
# Uso:
#   bash scripts/start-local.sh
#
# Se ejecuta siempre desde la raiz del repo (o desde cualquier lado, el
# script se ubica solo).

set -e
cd "$(dirname "$0")/.."

echo "==> Levantando servicios..."
docker compose --env-file .env -f compose/docker-compose.local.yml up -d

echo "==> Renovando el tunel de Cloudflare (siempre se recrea, es gratis y rapido)..."
docker compose -f compose/docker-compose.local.yml up -d --force-recreate cloudflared

echo "==> Esperando a que el tunel entregue su URL..."
sleep 6

NEW_URL=""
for i in 1 2 3 4 5; do
  NEW_URL=$(docker compose -f compose/docker-compose.local.yml logs cloudflared 2>/dev/null \
    | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)
  if [ -n "$NEW_URL" ]; then
    break
  fi
  sleep 3
done

if [ -z "$NEW_URL" ]; then
  echo "No se pudo leer la URL del tunel automaticamente."
  echo "Revisa manualmente con:"
  echo "  docker compose -f compose/docker-compose.local.yml logs cloudflared | grep trycloudflare"
  exit 1
fi

HOST=$(echo "$NEW_URL" | sed 's|https://||')
echo "==> Nueva URL del tunel: $NEW_URL"

sed -i.bak "s|^N8N_HOST=.*|N8N_HOST=${HOST}|" .env
sed -i.bak "s|^WEBHOOK_URL=.*|WEBHOOK_URL=${NEW_URL}/|" .env
rm -f .env.bak

echo "==> Reiniciando n8n con la configuracion nueva..."
docker compose --env-file .env -f compose/docker-compose.local.yml up -d --force-recreate n8n

echo ""
echo "Listo. El bot deberia estar respondiendo en unos 5-10 segundos."
echo "URL actual: $NEW_URL"
