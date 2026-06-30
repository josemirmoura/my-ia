#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
source .env
set +a

docker compose up -d ollama
docker compose exec ollama ollama pull "${MY_IA_MODEL:-qwen3:1.7b}"

