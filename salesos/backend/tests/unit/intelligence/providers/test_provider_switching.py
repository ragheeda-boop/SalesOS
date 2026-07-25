"""Provider switching tests — factory, failover, router."""
from __future__ import annotations

import pytest

from intelligence.providers import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    ProviderFactory,
    QueryRouter,
    ComplexityLevel,
    OpenAIProvider,
    AnthropicProvider,
)


class MockProvider:
    def __init__(self, name="mock", model="mock-model"):
        self._name = name
        self._model = model

    @property
    def model_name(self):
        return self._model

    @property
    def provider_name(self):
        return self._name

    async def chat(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            content=f"Mock response from {self._name}",
            model=self._model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason=FinishReason.STOP,
            latency_ms=5.0,
            cost=0.001,
        )

    async def chat_stream(self, request: ChatRequest):
        yield {"type": "chunk", "content": "mock "}
        yield {"type": "chunk", "content": "stream"}
        yield {"type": "done"}

    async def embed(self, request):
        from intelligence.providers import EmbeddingResponse
        return EmbeddingResponse(embedding=[0.1, 0.2, 0.3], model="mock-embed")


def test_factory_create_openai():
    provider = ProviderFactory.create("openai", api_key="test-key")
    assert provider.provider_name == "openai"
    assert isinstance(provider, OpenAIProvider)


def test_factory_create_anthropic():
    provider = ProviderFactory.create("anthropic", api_key="test-key")
    assert provider.provider_name == "anthropic"
    assert isinstance(provider, AnthropicProvider)


def test_factory_register_and_switch():
    ProviderFactory.register("mock_switch", MockProvider)
    provider = ProviderFactory.create("mock_switch")
    assert provider.provider_name == "mock"

    ProviderFactory.register("mock_switch2", MockProvider)
    provider2 = ProviderFactory.create("mock_switch2")
    assert provider2 is not None


def test_factory_create_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        ProviderFactory.create("nonexistent")


def test_factory_all_providers():
    configs = [
        ("openai", {"api_key": "test-key"}),
        ("anthropic", {"api_key": "test-key"}),
        ("gemini", {"api_key": "test-key"}),
        ("azure", {"api_key": "test-key", "azure_endpoint": "https://test.openai.azure.com"}),
        ("ollama", {}),
    ]
    for name, kwargs in configs:
        provider = ProviderFactory.create(name, **kwargs)
        assert provider is not None
        assert provider.provider_name == name


def test_factory_create_from_settings_default():
    provider = ProviderFactory.create_from_settings(provider_type="openai", api_key="test-key")
    assert provider.provider_name == "openai"


def test_factory_create_from_settings_anthropic():
    provider = ProviderFactory.create_from_settings(provider_type="anthropic", api_key="test-key")
    assert provider.provider_name == "anthropic"


def test_router_route_with_preferred():
    decision = QueryRouter.route(
        messages=[{"role": "user", "content": "analyze this data"}],
        preferred_provider="anthropic",
    )
    assert decision.provider == "anthropic"


def test_router_complexity_levels():
    simple = QueryRouter.classify_complexity(messages=[{"role": "user", "content": "hi"}])
    assert simple == ComplexityLevel.SIMPLE

    moderate = QueryRouter.classify_complexity(messages=[{"role": "user", "content": "Explain the difference between AI and ML in detail"}])
    assert moderate == ComplexityLevel.MODERATE

    complex_tools = QueryRouter.classify_complexity(messages=[{"role": "user", "content": "Analyze"}], tools=[{"function": {"name": "test"}}])
    assert complex_tools == ComplexityLevel.COMPLEX


@pytest.mark.asyncio
async def test_openai_no_api_key():
    provider = OpenAIProvider(api_key=None)
    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "hi"}]))
    assert response.finish_reason == FinishReason.ERROR


@pytest.mark.asyncio
async def test_anthropic_no_api_key():
    provider = AnthropicProvider(api_key=None)
    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "hi"}]))
    assert response.finish_reason == FinishReason.ERROR


def test_failover_chain_order():
    chain = ProviderFactory.FAILOVER_CHAIN
    assert chain[0] == "openai"
    assert chain[1] == "anthropic"
    assert chain[2] == "gemini"
