# my-ia

API local para uma LLM pequena, CPU-only, voltada a respostas curtas de atendimento via WhatsApp.

## Decisao inicial

- Runtime: Ollama, por ser o caminho mais simples e rapido para operar uma unica LLM.
- Modelo: `qwen3:1.7b`, equilibrio entre velocidade e qualidade em CPU.
- API publica dos sistemas: `my-ia-api`, compativel com o formato basico de `/v1/chat/completions`.
- LLM: privada na rede Docker, sem porta publicada.
- Porta local inicial: `127.0.0.1:18081`.

## Operacao

Subir servicos:

```bash
docker compose up -d --build
```

Baixar ou atualizar o modelo:

```bash
./scripts/pull-model.sh
```

Testar:

```bash
./scripts/smoke-test.sh
```

Ver logs:

```bash
docker compose logs -f api ollama
```

## Uso

```bash
curl http://127.0.0.1:18081/v1/chat/completions \
  -H "Authorization: Bearer $MY_IA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "Responda em pt-BR, curto e adequado para WhatsApp."},
      {"role": "user", "content": "Ola, voces fazem atendimento comercial?"}
    ],
    "max_tokens": 160,
    "temperature": 0.2
  }'
```

## Limites iniciais

- Ollama: ate 2 vCPU e 3 GiB.
- API: ate 0.5 vCPU e 256 MiB.
- Um modelo carregado por vez.
- Paralelismo do Ollama: 1.

Esses limites protegem os demais servicos da VPS. Para expor por dominio, colocar Traefik na frente da API e manter o Ollama privado.
