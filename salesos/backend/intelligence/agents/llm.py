"""LLM service abstraction — now wraps the unified provider layer."""

from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from sdk.config import sdk_settings

from intelligence.providers import (
    ChatRequest,
    ChatResponse as ProviderChatResponse,
    LLMProvider,
    ProviderFactory,
    get_provider,
    StreamEvent,
    CostTracker,
    get_cost_tracker,
)


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    cost: float = 0.0
    latency_ms: float = 0.0


class LLMService:
    """Unified LLM service that delegates to the provider layer.

    All agent code uses this service. Provider selection is done
    via the ProviderFactory, enabling zero-code provider switching.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        provider_type: str | None = None,
        cost_tracker: CostTracker | None = None,
    ):
        self._provider_type = provider_type
        self._model_override = model
        self._api_key_override = api_key
        self._cost_tracker = cost_tracker or get_cost_tracker()

    def _get_provider(self) -> LLMProvider:
        kwargs: dict[str, Any] = {}
        if self._api_key_override:
            kwargs["api_key"] = self._api_key_override
        if self._model_override:
            kwargs["model"] = self._model_override
        return get_provider(provider_type=self._provider_type, **kwargs)

    async def chat(
        self,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tenant_id: str | None = None,
    ) -> LLMResponse:
        provider = self._get_provider()

        request = ChatRequest(
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or self._model_override,
            response_format=response_format,
            tools=tools,
            tenant_id=tenant_id,
        )

        response: ProviderChatResponse = await provider.chat(request)

        self._cost_tracker.track(
            provider=provider.provider_name,
            model=response.model,
            prompt_tokens=response.usage.get("prompt_tokens", 0),
            completion_tokens=response.usage.get("completion_tokens", 0),
            operation="chat",
            tenant_id=tenant_id,
            latency_ms=response.latency_ms,
        )

        return LLMResponse(
            content=response.content,
            model=response.model,
            usage=response.usage,
            finish_reason=response.finish_reason.value,
            cost=response.cost,
            latency_ms=response.latency_ms,
        )

    async def chat_stream(
        self,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> AsyncIterator[StreamEvent]:
        provider = self._get_provider()

        request = ChatRequest(
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or self._model_override,
            stream=True,
        )

        async for event in provider.chat_stream(request):
            yield event

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        from intelligence.providers import EmbeddingRequest
        provider = self._get_provider()
        request = EmbeddingRequest(text=text, model=model)
        response = await provider.embed(request)

        self._cost_tracker.track(
            provider=provider.provider_name,
            model=response.model,
            prompt_tokens=response.usage.get("prompt_tokens", 0),
            completion_tokens=0,
            operation="embed",
        )

        if isinstance(response.embedding, list) and response.embedding and isinstance(response.embedding[0], float):
            return response.embedding
        return response.embedding[0] if isinstance(response.embedding, list) and response.embedding else []
