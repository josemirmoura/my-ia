import os
import re
import time
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


API_KEY = os.environ["MY_IA_API_KEY"]
MODEL = os.getenv("MY_IA_MODEL", "gemma3:1b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "1800"))
DEFAULT_NUM_CTX = int(os.getenv("DEFAULT_NUM_CTX", "2048"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "10000"))
DEFAULT_NUM_THREAD = int(os.getenv("DEFAULT_NUM_THREAD", "1"))
DEFAULT_SYSTEM_PROMPT = os.getenv(
    "DEFAULT_SYSTEM_PROMPT",
    "Voce e um atendente de WhatsApp. Responda em portugues do Brasil, "
    "com tom profissional, cordial, objetivo e seguro. Use 1 ou 2 frases em respostas simples. "
    "Quando o usuario pedir dicas, passos ou lista, use no maximo 3 itens curtos e conclua a resposta. "
    "Nao use emojis, girias, brincadeiras ou linguagem excessivamente informal. "
    "Nao invente informacoes; se faltar contexto, peca a informacao necessaria. "
    "Nao use bom dia, boa tarde ou boa noite, a menos que o usuario ja tenha usado. "
    "Nao mostre raciocinio interno.",
)

app = FastAPI(title="my-ia", version="0.1.0")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    temperature: float | None = None
    stream: bool = False
    max_tokens: int | None = None


def require_auth(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


def openai_response(content: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> dict[str, Any]:
    created = int(time.time())
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def normalize_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    normalized = [message.model_dump() for message in messages]
    has_system = any(message.get("role") == "system" for message in normalized)
    if not has_system:
        normalized.insert(0, {"role": "system", "content": DEFAULT_SYSTEM_PROMPT})
    return normalized


def clean_content(content: str) -> str:
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
    return content.strip()


@app.get("/health")
async def health() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
        ollama = "ok"
    except Exception:
        ollama = "unavailable"
    return {"status": "ok", "model": MODEL, "ollama": ollama}


@app.get("/v1/models")
async def models(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL,
                "object": "model",
                "owned_by": "my-ia",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    require_auth(authorization)
    if payload.stream:
        raise HTTPException(status_code=400, detail="Streaming is not enabled in this gateway yet")
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages is required")

    selected_model = payload.model or MODEL
    options: dict[str, Any] = {
        "num_ctx": DEFAULT_NUM_CTX,
        "temperature": payload.temperature if payload.temperature is not None else DEFAULT_TEMPERATURE,
        "num_predict": payload.max_tokens or DEFAULT_MAX_TOKENS,
        "num_thread": DEFAULT_NUM_THREAD,
    }

    ollama_payload = {
        "model": selected_model,
        "messages": normalize_messages(payload.messages),
        "stream": False,
        "think": False,
        "options": options,
        "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "24h"),
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=ollama_payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc.response.text[:300]}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama unavailable: {exc}") from exc

    message = data.get("message", {})
    content = clean_content(message.get("content") or "")
    result = openai_response(
        content=content,
        model=selected_model,
        prompt_tokens=int(data.get("prompt_eval_count") or 0),
        completion_tokens=int(data.get("eval_count") or 0),
    )
    result["metadata"] = {
        "total_duration_ns": data.get("total_duration"),
        "load_duration_ns": data.get("load_duration"),
        "client": request.client.host if request.client else None,
    }
    return JSONResponse(result)
