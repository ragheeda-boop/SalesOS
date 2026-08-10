from __future__ import annotations

import json
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


class AnthropicProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        base_url: str | None = None,
    ):
        self._api_key = api_key
        self.default_model = model
        self._base_url = base_url
        self._client = None

    @property
    def model_name(self) -> str:
        return self.default_model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def _get_client(self):
        if self._client is None and self._api_key:
            try:
                from anthropic import AsyncAnthropic
                kwargs = {"api_key": self._api_key}
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = AsyncAnthropic(**kwargs)
            except ImportError:
                pass
        return self._client

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.monotonic()
        client = await self._get_client()
        if not client:
            return ChatResponse(content="", model=self.default_model, finish_reason=FinishReason.ERROR)

        msgs = self._build_messages(request)
        system = request.system

        kwargs: dict[str, Any] = {"model": request.model or self.default_model, "messages": msgs}
        if system:
            kwargs["system"] = system
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        else:
            kwargs["max_tokens"] = 4096
        if request.stop:
            kwargs["stop_sequences"] = request.stop

        response = await client.messages.create(**kwargs)
        elapsed = (time.monotonic() - start) * 1000

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        usage = {
            "prompt_tokens": response.usage.input_tokens if response.usage else 0,
            "completion_tokens": response.usage.output_tokens if response.usage else 0,
            "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
        }
        cost = estimate_cost(response.model, usage["prompt_tokens"], usage["completion_tokens"])

        elapsed_ms = round(elapsed, 2)
        return ChatResponse(
            content=content,
            model=response.model,
            usage=usage,
            finish_reason=self._map_finish(response.stop_reason),
            latency_ms=elapsed_ms,
            cost=cost,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        client = await self._get_client()
        if not client:
            yield StreamEvent(type="error", error="No API key configured")
            return

        msgs = self._build_messages(request)
        system = request.system

        kwargs: dict[str, Any] = {
            "model": request.model or self.default_model,
            "messages": msgs,
            "max_tokens": request.max_tokens or 4096,
            "stream": True,
        }
        if system:
            kwargs["system"] = system
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield StreamEvent(type="chunk", content=text)

        final = await stream.get_final_message()
        usage = {}
        if final.usage:
            usage = {
                "prompt_tokens": final.usage.input_tokens or 0,
                "completion_tokens": final.usage.output_tokens or 0,
                "total_tokens": (final.usage.input_tokens + final.usage.output_tokens) or 0,
            }
        yield StreamEvent(
            type="done",
            finish_reason=self._map_finish(final.stop_reason),
            usage=usage,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise NotImplementedError("Anthropic does not provide embedding API")

    def _build_messages(self, request: ChatRequest) -> list[dict[str, Any]]:
        return request.messages or []

    def _map_finish(self, reason: str | None) -> FinishReason:
        mapping = {
            "end_turn": FinishReason.STOP,
            "max_tokens": FinishReason.LENGTH,
            "stop_sequence": FinishReason.STOP,
            "tool_use": FinishReason.TOOL_CALLS,
        }
        return mapping.get(reason or "", FinishReason.STOP)
