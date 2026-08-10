from __future__ import annotations

import time
from typing import Any, AsyncIterator

from openai import AsyncAzureOpenAI

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


class AzureOpenAIProvider:
    def __init__(
        self,
        api_key: str | None = None,
        azure_endpoint: str | None = None,
        api_version: str = "2024-06-01",
        deployment: str = "gpt-4o-mini",
    ):
        self._api_key = api_key
        self._azure_endpoint = azure_endpoint
        self._api_version = api_version
        self.default_model = deployment
        self._client = None

    @property
    def model_name(self) -> str:
        return self.default_model

    @property
    def provider_name(self) -> str:
        return "azure"

    async def _get_client(self):
        if self._client is None and self._api_key and self._azure_endpoint:
            try:
                self._client = AsyncAzureOpenAI(
                    api_key=self._api_key,
                    azure_endpoint=self._azure_endpoint,
                    api_version=self._api_version,
                )
            except Exception:
                pass
        return self._client

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.monotonic()
        client = await self._get_client()
        if not client:
            return ChatResponse(content="", model=self.default_model, finish_reason=FinishReason.ERROR)

        msgs = self._build_messages(request)
        kwargs = self._build_kwargs(request)

        response = await client.chat.completions.create(
            model=request.model or self.default_model,
            messages=msgs,
            **kwargs,
        )
        choice = response.choices[0]
        elapsed = (time.monotonic() - start) * 1000

        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }
        cost = estimate_cost(response.model, usage["prompt_tokens"], usage["completion_tokens"])

        elapsed_ms = round(elapsed, 2)
        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage,
            finish_reason=self._map_finish(choice.finish_reason),
            latency_ms=elapsed_ms,
            cost=cost,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        client = await self._get_client()
        if not client:
            yield StreamEvent(type="error", error="Azure OpenAI not configured")
            return

        msgs = self._build_messages(request)
        kwargs = self._build_kwargs(request)
        kwargs.pop("response_format", None)

        stream = await client.chat.completions.create(
            model=request.model or self.default_model,
            messages=msgs,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield StreamEvent(type="chunk", content=delta.content)

            if chunk.choices and chunk.choices[0].finish_reason:
                usage = {}
                if chunk.usage:
                    usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens or 0,
                        "completion_tokens": chunk.usage.completion_tokens or 0,
                        "total_tokens": chunk.usage.total_tokens or 0,
                    }
                yield StreamEvent(
                    type="done",
                    finish_reason=self._map_finish(chunk.choices[0].finish_reason),
                    usage=usage,
                )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        client = await self._get_client()
        if not client:
            model = request.model or "text-embedding-3-large"
            return EmbeddingResponse(embedding=[], model=model)

        model = request.model or "text-embedding-3-large"
        texts = request.text if isinstance(request.text, list) else [request.text]
        response = await client.embeddings.create(model=model, input=texts)

        embeddings = [d.embedding for d in response.data]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        return EmbeddingResponse(
            embedding=embeddings if isinstance(request.text, list) else embeddings[0],
            model=response.model,
            usage=usage,
        )

    def _build_messages(self, request: ChatRequest) -> list[dict[str, Any]]:
        msgs: list[dict[str, Any]] = []
        if request.system:
            msgs.append({"role": "system", "content": request.system})
        if request.messages:
            msgs.extend(request.messages)
        return msgs

    def _build_kwargs(self, request: ChatRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if request.response_format:
            kwargs["response_format"] = request.response_format
        if request.tools:
            kwargs["tools"] = request.tools
        if request.stop:
            kwargs["stop"] = request.stop
        return kwargs

    def _map_finish(self, reason: str | None) -> FinishReason:
        mapping = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "tool_calls": FinishReason.TOOL_CALLS,
            "content_filter": FinishReason.CONTENT_FILTER,
        }
        return mapping.get(reason or "", FinishReason.STOP)
