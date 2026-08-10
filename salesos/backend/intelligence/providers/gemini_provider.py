from __future__ import annotations

import time
from typing import Any, AsyncIterator

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


class GeminiProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
    ):
        self._api_key = api_key
        self.default_model = model
        self._client = None

    @property
    def model_name(self) -> str:
        return self.default_model

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def _get_client(self):
        if self._client is None and self._api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._client = genai
            except ImportError:
                pass
        return self._client

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.monotonic()
        client = await self._get_client()
        if not client:
            return ChatResponse(content="", model=self.default_model, finish_reason=FinishReason.ERROR)

        model_name = request.model or self.default_model
        gen_model = client.GenerativeModel(model_name)

        content_parts = []
        if request.system:
            gen_model = client.GenerativeModel(model_name, system_instruction=request.system)

        if request.messages:
            for msg in request.messages:
                content_parts.append({"role": msg["role"], "parts": [msg["content"]]})

        kwargs: dict[str, Any] = {}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_output_tokens"] = request.max_tokens

        try:
            response = await gen_model.generate_content_async(
                content_parts or "Hello",
                generation_config=kwargs,
            )
        except Exception:
            return ChatResponse(content="", model=model_name, finish_reason=FinishReason.ERROR)

        elapsed = (time.monotonic() - start) * 1000

        content = response.text or ""
        finish = FinishReason.STOP
        if response.candidates and response.candidates[0].finish_reason:
            finish = self._map_finish(response.candidates[0].finish_reason)

        usage = {}
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                "completion_tokens": response.usage_metadata.candidates_token_count or 0,
                "total_tokens": response.usage_metadata.total_token_count or 0,
            }

        cost = estimate_cost(model_name, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

        elapsed_ms = round(elapsed, 2)
        return ChatResponse(
            content=content,
            model=model_name,
            usage=usage,
            finish_reason=finish,
            latency_ms=elapsed_ms,
            cost=cost,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        client = await self._get_client()
        if not client:
            yield StreamEvent(type="error", error="No API key configured")
            return

        model_name = request.model or self.default_model
        gen_model = client.GenerativeModel(model_name)

        content_parts = []
        if request.system:
            gen_model = client.GenerativeModel(model_name, system_instruction=request.system)

        if request.messages:
            for msg in request.messages:
                content_parts.append({"role": msg["role"], "parts": [msg["content"]]})

        kwargs: dict[str, Any] = {}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_output_tokens"] = request.max_tokens

        try:
            response = await gen_model.generate_content_async(
                content_parts or "Hello",
                generation_config=kwargs,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield StreamEvent(type="chunk", content=chunk.text)

                if chunk.candidates and chunk.candidates[0].finish_reason:
                    usage = {}
                    if chunk.usage_metadata:
                        usage = {
                            "prompt_tokens": chunk.usage_metadata.prompt_token_count or 0,
                            "completion_tokens": chunk.usage_metadata.candidates_token_count or 0,
                            "total_tokens": chunk.usage_metadata.total_token_count or 0,
                        }
                    yield StreamEvent(
                        type="done",
                        finish_reason=self._map_finish(chunk.candidates[0].finish_reason),
                        usage=usage,
                    )
                    return
        except Exception:
            yield StreamEvent(type="error", error="Gemini streaming failed")
            return

        yield StreamEvent(type="done")

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        client = await self._get_client()
        if not client:
            model = request.model or "text-embedding-004"
            return EmbeddingResponse(embedding=[], model=model)

        model_name = request.model or "text-embedding-004"
        texts = request.text if isinstance(request.text, list) else [request.text]

        result = await client.embed_content_async(
            model=model_name,
            content=texts if len(texts) > 1 else texts[0],
        )

        embeddings = result.get("embedding", [])
        if isinstance(texts, str):
            embeddings = embeddings if isinstance(embeddings[0], float) else [embeddings[0] if isinstance(embeddings, list) and len(embeddings) > 0 else embeddings]

        return EmbeddingResponse(
            embedding=embeddings if isinstance(request.text, list) else (embeddings[0] if isinstance(embeddings, list) and len(embeddings) > 0 else embeddings),
            model=model_name,
        )

    def _map_finish(self, reason: int | str | None) -> FinishReason:
        gemini_map = {
            1: FinishReason.STOP,
            2: FinishReason.LENGTH,
            3: FinishReason.CONTENT_FILTER,
            4: FinishReason.ERROR,
        }
        if isinstance(reason, int):
            return gemini_map.get(reason, FinishReason.STOP)
        return FinishReason.STOP
