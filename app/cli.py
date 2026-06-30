import json
import urllib.error
import urllib.request


def load_env(path: str) -> dict[str, str]:
    values = {}
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value
    return values


def main() -> None:
    env = load_env(".env")
    api_key = env["MY_IA_API_KEY"]
    bind = env.get("MY_IA_BIND", "127.0.0.1")
    port = env.get("MY_IA_PORT", "18081")
    url = f"http://{bind}:{port}/v1/chat/completions"

    messages = [
        {
            "role": "system",
            "content": (
                "Voce e um atendente de WhatsApp. Responda em portugues do Brasil, "
                "com tom cordial, direto e levemente animado. Use 1 ou 2 frases em respostas simples. "
                "Quando o usuario pedir dicas, passos ou lista, use no maximo 3 itens curtos e conclua a resposta. "
                "Use no maximo um emoji, e somente quando combinar com a resposta. "
                "Nao invente informacoes; se faltar contexto, peca a informacao necessaria. "
                "Nao use bom dia, boa tarde ou boa noite, a menos que o usuario ja tenha usado. "
                "Nao mostre raciocinio interno."
            ),
        }
    ]

    print("Chat my-ia. Digite 'sair' para encerrar.")

    while True:
        try:
            text = input("\nvoce> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.lower() in {"sair", "exit", "quit"}:
            break
        if not text:
            continue

        messages.append({"role": "user", "content": text})
        payload = {
            "messages": messages[-9:],
            "max_tokens": 100,
            "temperature": 0.45,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            print(f"erro> HTTP {error.code}: {error.read().decode('utf-8')[:300]}")
            continue
        except Exception as error:
            print(f"erro> {error}")
            continue

        answer = data["choices"][0]["message"]["content"].strip()
        print(f"ia> {answer}")
        messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
