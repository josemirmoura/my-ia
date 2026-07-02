# Configuracao my-ia para parceiro

Este pacote cria uma API local de LLM para atendimento via WhatsApp, usando CPU, Docker Compose, Ollama e um gateway FastAPI compativel com o formato basico de `/v1/chat/completions`.

## Objetivo

- Respostas curtas para atendimento.
- Tom profissional, cordial, objetivo e seguro.
- Sem emojis, girias ou informalidade excessiva por padrao.
- Baixo impacto em VPS sem GPU.
- LLM privada; somente o gateway da API deve ser exposto para outros sistemas.

## Stack

- Docker + Docker Compose.
- Ollama como runtime local de modelo.
- Modelo: `gemma3:1b`.
- Gateway API: FastAPI + Uvicorn.
- Endpoint principal: `/v1/chat/completions`.
- Autenticacao: `Authorization: Bearer <MY_IA_API_KEY>`.

## Limites operacionais

Servico `ollama`:

- CPU: `1.0`
- Memoria: `2g`
- Modelos carregados: `1`
- Paralelismo: `1`
- Porta: privada na rede Docker, sem publicacao direta.

Servico `api`:

- CPU: `0.5`
- Memoria: `256m`
- Porta local padrao: `127.0.0.1:18081`

Defaults do modelo:

- `MY_IA_MODEL=gemma3:1b`
- `DEFAULT_NUM_CTX=2048`
- `DEFAULT_MAX_TOKENS=200`
- `DEFAULT_TEMPERATURE=0.3`
- `DEFAULT_NUM_THREAD=1`
- `REQUEST_TIMEOUT_SECONDS=35`

## Prompt padrao

```text
Voce e um atendente de WhatsApp. Responda em portugues do Brasil, com tom profissional, cordial, objetivo e seguro. Use 1 ou 2 frases em respostas simples. Quando o usuario pedir dicas, passos ou lista, use no maximo 3 itens curtos e conclua a resposta. Nao use emojis, girias, brincadeiras ou linguagem excessivamente informal. Nao invente informacoes; se faltar contexto, peca a informacao necessaria. Nao use bom dia, boa tarde ou boa noite, a menos que o usuario ja tenha usado. Nao mostre raciocinio interno.
```

## Instalacao

No servidor do parceiro:

```bash
cd /opt
unzip my-ia-partner.zip
cd my-ia
cp .env.example .env
```

Gerar uma chave:

```bash
API_KEY="$(openssl rand -hex 32)"
sed -i "s/^MY_IA_API_KEY=.*/MY_IA_API_KEY=${API_KEY}/" .env
chmod 600 .env
```

Subir os servicos:

```bash
docker compose up -d --build
```

Baixar o modelo:

```bash
./scripts/pull-model.sh
```

Testar:

```bash
./scripts/smoke-test.sh
```

Conversar pelo terminal:

```bash
./scripts/chat.sh
```

## Chamada da API

```bash
source .env

curl http://127.0.0.1:18081/v1/chat/completions \
  -H "Authorization: Bearer $MY_IA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Cliente perguntou se tem atendimento hoje. Responda como WhatsApp."}
    ]
  }'
```

## Exposicao externa

Nao exponha o Ollama diretamente.

Para uso por sistemas externos, publique apenas o servico `api`, preferencialmente atras de proxy reverso com HTTPS, por exemplo Traefik ou Nginx. O endpoint interno local e:

```text
http://127.0.0.1:18081
```

Em producao, usar dominio HTTPS dedicado, mantendo o header:

```text
Authorization: Bearer <MY_IA_API_KEY>
```

## Operacao

Ver status:

```bash
docker compose ps
```

Ver logs:

```bash
docker compose logs -f api ollama
```

Ver modelos instalados:

```bash
docker compose exec ollama ollama list
```

Parar:

```bash
docker compose stop
```

Atualizar build da API:

```bash
docker compose up -d --build api
```

## Observacoes

- Esta configuracao e para VPS sem GPU.
- O primeiro request apos carga ou troca de modelo pode demorar mais.
- O modelo fica carregado por `OLLAMA_KEEP_ALIVE=24h`, reduzindo cold start.
- Para respostas mais longas, aumente `DEFAULT_MAX_TOKENS` com cuidado.
- Para mais memoria de conversa, aumente `DEFAULT_NUM_CTX` com cuidado.
- Para menor impacto em CPU, mantenha `DEFAULT_NUM_THREAD=1` e `cpus: "1.0"` no Ollama.
