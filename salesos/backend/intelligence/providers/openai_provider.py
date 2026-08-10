from __future__ import annotations

import time
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

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


class OpenAIProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        organization: str | None = None,
    ):
        self._api_key = api_key
        self.default_model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=organization,
        ) if api_key else None
        self._base_url = base_url
        self._organization = organization

    @property
    def model_name(self) -> str:
        return self.default_model

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.monotonic()
        if not self._client:
            return ChatResponse(content="", model=self.default_model, finish_reason=FinishReason.ERROR)

        msgs = self._build_messages(request)
        kwargs = self._build_kwargs(request)

        response = await self._client.chat.completions.create(
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
            tool_calls=self._parse_tool_calls(choice.message.tool_calls) if choice.message.tool_calls else [],
            latency_ms=elapsed_ms,
            cost=cost,
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        if not self._client:
            yield StreamEvent(type="error", error="No API key configured")
            return

        msgs = self._build_messages(request)
        kwargs = self._build_kwargs(request)
        kwargs.pop("response_format", None)
        kwargs.pop("tools", None)

        stream = await self._client.chat.completions.create(
            model=request.model or self.default_model,
            messages=msgs,
            stream=True,
            stream_options={"include_usage": True},
            **kwargs,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield StreamEvent(type="chunk", content=delta.content)

            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    yield StreamEvent(type="tool_call", tool_calls=[{"id": tc.id, "function": tc.function.model_dump() if tc.function else {}}])

            if chunk.choices and chunk.choices[0].finish_reason:
                usage = {}
                if chunk.usage:
                    usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens or 0,
                        "completion_tokens": chunk.usage.completion_tokens or 0,
                        "total_tokens": chunk.usage.total_tokens or 0,
                    }
                if chunk.usage or chunk.choices[0].finish_reason:
                    yield StreamEvent(
                        type="done",
                        finish_reason=self._map_finish(chunk.choices[0].finish_reason),
                        usage=usage,
                    )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        if not self._client:
            model = request.model or "text-embedding-3-large"
            if isinstance(request.text, list):
                return EmbeddingResponse(embedding=[[]], model=model)
            return EmbeddingResponse(embedding=[], model=model)

        model = request.model or "text-embedding-3-large"
        texts = request.text if isinstance(request.text, list) else [request.text]
        response = await self._client.embeddings.create(model=model, input=texts)

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

    def _parse_tool_calls(self, tool_calls: Any) -> list[dict[str, Any]]:
        return [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]
