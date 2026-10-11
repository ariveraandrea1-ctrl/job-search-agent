#!/bin/bash
# start-local.sh
#
# Levanta todo el entorno local (n8n, postgres, minio, mailpit, profile-api,
# cloudflared) y renueva automaticamente el tunel de Cloudflare, que expira
# cada vez que se apaga el Mac o se reinicia Docker. Al final revisa que
# Telegram haya quedado con la URL nueva del tunel (BUG-36).
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
docker compose --env-file .env -f compose/docker-compose.local.yml up -d --force-recreate cloudflared

echo "==> Esperando a que el tunel entregue su URL..."
sleep 6

NEW_URL=""
for i in 1 2 3 4 5; do
  NEW_URL=$(docker compose --env-file .env -f compose/docker-compose.local.yml logs cloudflared 2>/dev/null \
    | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)
  if [ -n "$NEW_URL" ]; then
    break
  fi
  sleep 3
done

if [ -z "$NEW_URL" ]; then
  echo "No se pudo leer la URL del tunel automaticamente."
  echo "Revisa manualmente con:"
  echo "  docker compose --env-file .env -f compose/docker-compose.local.yml logs cloudflared | grep trycloudflare"
  exit 1
fi

HOST=$(echo "$NEW_URL" | sed 's|https://||')
echo "==> Nueva URL del tunel: $NEW_URL"

sed -i.bak "s|^N8N_HOST=.*|N8N_HOST=${HOST}|" .env
sed -i.bak "s|^WEBHOOK_URL=.*|WEBHOOK_URL=${NEW_URL}/|" .env
rm -f .env.bak

# Antes de reiniciar n8n espero a que la URL nueva responda desde internet.
# Si n8n arranca antes, le pide a Telegram que use una URL que todavia no
# existe, Telegram la rechaza y el bot queda sin webhook (BUG-36).
echo "==> Esperando a que el tunel responda desde internet..."
TUNEL_OK=""
for i in $(seq 1 20); do
  CODIGO=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$NEW_URL/healthz" || true)
  if [ "$CODIGO" = "200" ]; then
    TUNEL_OK="si"
    break
  fi
  sleep 3
done
if [ -z "$TUNEL_OK" ]; then
  echo "El tunel no respondio despues de 60 segundos (ultimo codigo: $CODIGO)."
  echo "Vuelve a correr este script en un par de minutos."
  exit 1
fi

TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2-)

# Reinicia n8n, espera a que este arriba y revisa que Telegram tenga la URL
# nueva. Devuelve 0 si quedo bien.
reiniciar_n8n_y_revisar() {
  docker compose --env-file .env -f compose/docker-compose.local.yml up -d --force-recreate n8n

  for i in $(seq 1 30); do
    if curl -s -o /dev/null --max-time 3 http://localhost:5678/healthz; then
      break
    fi
    sleep 2
  done

  # n8n registra el webhook unos segundos despues de arrancar.
  for i in $(seq 1 10); do
    sleep 3
    INFO=$(curl -s --max-time 10 "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" || true)
    if echo "$INFO" | grep -q "$HOST"; then
      return 0
    fi
  done
  return 1
}

echo "==> Reiniciando n8n con la configuracion nueva..."
if ! reiniciar_n8n_y_revisar; then
  echo "==> Telegram todavia no tiene la URL nueva. Reintento una vez..."
  if ! reiniciar_n8n_y_revisar; then
    echo ""
    echo "ATENCION: el bot NO va a recibir mensajes."
    echo "Telegram no tiene registrada la URL del tunel. Lo que respondio:"
    echo "$INFO"
    echo ""
    echo "Para arreglarlo a mano: en n8n desactiva y vuelve a activar el flujo"
    echo "telegram-invitacion, y revisa de nuevo con getWebhookInfo"
    echo "(ver docs/runbooks/entorno-local.md)."
    exit 1
  fi
fi

echo ""
echo "Listo. Telegram ya tiene la URL nueva y el bot puede recibir mensajes."
echo "URL actual: $NEW_URL"
