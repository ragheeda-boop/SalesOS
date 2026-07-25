from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import httpx

from .base import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    FinishReason,
    StreamEvent,
    estimate_cost,
)
from .protocol import LLMProvider


OLLAMA_DEFAULT_BASE = "http://localhost:11434"


class OllamaProvider:
    def __init__(
        self,
        base_url: str = OLLAMA_DEFAULT_BASE,
        model: str = "llama3.2",
    ):
        self._base_url = base_url.rstrip("/")
        self.default_model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    @property
    def model_name(self) -> str:
        return self.default_model

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.monotonic()

        payload = self._build_payload(request)
        payload["stream"] = False

        try:
            response = await self._client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            return ChatResponse(content="", model=request.model or self.default_model, finish_reason=FinishReason.ERROR)

        elapsed = (time.monotonic() - start) * 1000
        content = data.get("message", {}).get("content", "")
        model_used = data.get("model", request.model or self.default_model)

        usage = {}
        if "prompt_eval_count" in data:
            usage["prompt_tokens"] = data["prompt_eval_count"]
        if "eval_count" in data:
            usage["completion_tokens"] = data["eval_count"]
        usage["total_tokens"] = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

        cost = 0.0  # Local models are free

        return ChatResponse(
            content=content,
            model=model_used,
            usage=usage,
            finish_reason=FinishReason.STOP,
            latency_ms=round(elapsed, 2),
            cost=cost,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        payload = self._build_payload(request)
        payload["stream"] = True

        try:
            async with self._client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if "message" in data and data["message"].get("content"):
                        yield StreamEvent(type="chunk", content=data["message"]["content"])

                    if data.get("done", False):
                        usage = {}
                        if "prompt_eval_count" in data:
                            usage["prompt_tokens"] = data["prompt_eval_count"]
                        if "eval_count" in data:
                            usage["completion_tokens"] = data["eval_count"]
                        yield StreamEvent(type="done", usage=usage)
                        return
        except Exception as exc:
            yield StreamEvent(type="error", error=str(exc))
            return

        yield StreamEvent(type="done")

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        texts = request.text if isinstance(request.text, list) else [request.text]
        model = request.model or self.default_model
        embeddings = []

        for text in texts:
            try:
                response = await self._client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": model, "prompt": text},
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data.get("embedding", []))
            except Exception:
                embeddings.append([])

        return EmbeddingResponse(
            embedding=embeddings if isinstance(request.text, list) else (embeddings[0] if embeddings else []),
            model=model,
        )

    def _build_payload(self, request: ChatRequest) -> dict[str, Any]:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        if request.messages:
            messages.extend(request.messages)

        payload: dict[str, Any] = {
            "model": request.model or self.default_model,
            "messages": messages,
        }
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}
        if request.max_tokens is not None:
            if "options" not in payload:
                payload["options"] = {}
            payload["options"]["num_predict"] = request.max_tokens
        return payload

    async def close(self):
        await self._client.aclose()
