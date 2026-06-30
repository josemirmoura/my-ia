#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
source .env
set +a

curl -fsS "http://${MY_IA_BIND:-127.0.0.1}:${MY_IA_PORT:-18080}/health"
printf '\n'

curl -fsS "http://${MY_IA_BIND:-127.0.0.1}:${MY_IA_PORT:-18080}/v1/chat/completions" \
  -H "Authorization: Bearer ${MY_IA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "Responda em português do Brasil, de forma curta, objetiva e útil para atendimento por WhatsApp."},
      {"role": "user", "content": "Diga uma saudação inicial para atendimento comercial."}
    ],
    "max_tokens": 40,
    "temperature": 0.45
  }'
printf '\n'
