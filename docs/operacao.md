# Operacao my-ia

## Endpoint

Local na VPS:

- `http://127.0.0.1:18081/health`
- `http://127.0.0.1:18081/v1/chat/completions`

Autenticacao:

- Header: `Authorization: Bearer <MY_IA_API_KEY>`

## Boas praticas para WhatsApp

- Usar mensagens curtas.
- Limitar `max_tokens` entre 80 e 200 no primeiro uso.
- Manter `temperature` entre 0.2 e 0.4 para atendimento.
- O gateway envia `think:false` ao Ollama para reduzir latencia e evitar respostas vazias em modelos Qwen3.
- Resumir historico longo antes de enviar para o modelo.
- Nao mandar anexos ou textos longos diretamente sem pre-processamento.

## Escala posterior

Quando houver volume real:

- adicionar fila de atendimento e controle de concorrencia por cliente;
- trocar o backend do gateway para outro provedor quando necessario;
- publicar a API por Traefik com dominio dedicado;
- mover o LLM para maquina com mais CPU/GPU sem mudar os sistemas consumidores.
