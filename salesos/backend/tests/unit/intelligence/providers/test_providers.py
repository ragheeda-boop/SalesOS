"""Provider tests — all 5 providers + factory + router + cost tracker."""
from __future__ import annotations

import pytest

from intelligence.providers import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    FinishReason,
    ProviderFactory,
    QueryRouter,
    ComplexityLevel,
    CostTracker,
    estimate_cost,
    get_model_family,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    AzureOpenAIProvider,
    OllamaProvider,
)


# ── Mock Provider for Testing ──────────────────────────────────────────────


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

    async def embed(self, request: EmbeddingRequest):
        from intelligence.providers import EmbeddingResponse
        return EmbeddingResponse(embedding=[0.1, 0.2, 0.3], model="mock-embed")


# ── ProviderFactory ────────────────────────────────────────────────────────


def test_factory_register_and_create():
    ProviderFactory.register("mock", MockProvider)
    provider = ProviderFactory.create("mock")
    assert provider.provider_name == "mock"
    assert provider.model_name == "mock-model"


def test_factory_create_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        ProviderFactory.create("nonexistent")


def test_factory_known_providers():
    provider_configs = [
        ("openai", {"api_key": "test-key"}),
        ("anthropic", {"api_key": "test-key"}),
        ("gemini", {"api_key": "test-key"}),
        ("azure", {"api_key": "test-key", "azure_endpoint": "https://test.openai.azure.com"}),
        ("ollama", {}),
    ]
    for name, kwargs in provider_configs:
        provider = ProviderFactory.create(name, **kwargs)
        assert provider is not None
        assert provider.provider_name == name


# ── Estimate Cost ──────────────────────────────────────────────────────────


def test_estimate_cost_known_model():
    cost = estimate_cost("gpt-4o-mini", 1000, 500)
    assert cost > 0
    assert cost < 1.0


def test_estimate_cost_unknown_model():
    cost = estimate_cost("unknown-model", 1000, 500)
    assert cost > 0


def test_estimate_cost_zero_tokens():
    cost = estimate_cost("gpt-4o", 0, 0)
    assert cost == 0.0


# ── Model Family ──────────────────────────────────────────────────────────


def test_get_model_family():
    assert get_model_family("gpt-4o") == "openai"
    assert get_model_family("claude-3-5-sonnet") == "anthropic"
    assert get_model_family("gemini-1.5-pro") == "gemini"
    assert get_model_family("azure-gpt-4") == "azure"
    assert get_model_family("llama3.2") == "ollama"


# ── OpenAI Provider ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_openai_no_api_key():
    provider = OpenAIProvider(api_key=None)
    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "hi"}]))
    assert response.finish_reason == FinishReason.ERROR
    assert response.content == ""


@pytest.mark.asyncio
async def test_openai_embed_no_key():
    provider = OpenAIProvider(api_key=None)
    response = await provider.embed(EmbeddingRequest(text="hello"))
    assert response.embedding == []


# ── Anthropic Provider ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_anthropic_no_api_key():
    provider = AnthropicProvider(api_key=None)
    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "hi"}]))
    assert response.finish_reason == FinishReason.ERROR


@pytest.mark.asyncio
async def test_anthropic_embed_not_implemented():
    provider = AnthropicProvider(api_key="test-key")
    with pytest.raises(NotImplementedError):
        await provider.embed(EmbeddingRequest(text="hello"))


# ── Gemini Provider ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gemini_no_api_key():
    provider = GeminiProvider(api_key=None)
    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "hi"}]))
    assert response.finish_reason == FinishReason.ERROR


@pytest.mark.asyncio
async def test_gemini_embed_no_key():
    provider = GeminiProvider(api_key=None)
    response = await provider.embed(EmbeddingRequest(text="hello"))
    assert response.embedding == []


# ── Azure Provider ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_azure_no_config():
    provider = AzureOpenAIProvider(api_key=None)
    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "hi"}]))
    assert response.finish_reason == FinishReason.ERROR


@pytest.mark.asyncio
async def test_azure_embed_no_key():
    provider = AzureOpenAIProvider(api_key=None)
    response = await provider.embed(EmbeddingRequest(text="hello"))
    assert response.embedding == []


# ── Ollama Provider ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ollama_default_url():
    provider = OllamaProvider()
    assert provider._base_url == "http://localhost:11434"
    assert provider.default_model == "llama3.2"


@pytest.mark.asyncio
async def test_ollama_custom_config():
    provider = OllamaProvider(base_url="http://10.0.0.1:11434", model="llama3.1")
    assert provider._base_url == "http://10.0.0.1:11434"
    assert provider.default_model == "llama3.1"


# ── Query Router ──────────────────────────────────────────────────────────


def test_router_classify_simple():
    level = QueryRouter.classify_complexity(messages=[{"role": "user", "content": "What is 2+2?"}])
    assert level == ComplexityLevel.SIMPLE


def test_router_classify_moderate():
    level = QueryRouter.classify_complexity(
        messages=[{"role": "user", "content": "Explain the key differences between" + " AI" * 50}]
    )
    assert level == ComplexityLevel.MODERATE


def test_router_classify_complex_with_tools():
    level = QueryRouter.classify_complexity(
        messages=[{"role": "user", "content": "Analyze this"}],
        tools=[{"type": "function", "function": {"name": "test"}}],
    )
    assert level == ComplexityLevel.COMPLEX


def test_router_classify_complex_with_code():
    level = QueryRouter.classify_complexity(
        messages=[{"role": "user", "content": "Write a Python function def calculate(x):"}]
    )
    assert level == ComplexityLevel.COMPLEX


def test_router_decision():
    decision = QueryRouter.route(messages=[{"role": "user", "content": "hi"}])
    assert decision.complexity == ComplexityLevel.SIMPLE
    assert decision.failover_chain
    assert decision.provider


def test_router_with_preferred():
    decision = QueryRouter.route(
        messages=[{"role": "user", "content": "analyze this data"}],
        preferred_provider="anthropic",
    )
    assert decision.provider == "anthropic"


# ── Cost Tracker ──────────────────────────────────────────────────────────


def test_cost_tracker_track():
    tracker = CostTracker()
    record = tracker.track(
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
        operation="chat",
    )
    assert record.provider == "openai"
    assert record.total_tokens == 150
    assert record.cost > 0
    assert record.success is True


def test_cost_tracker_budget():
    tracker = CostTracker()
    tracker.set_budget("tenant-1", 10.0)
    assert tracker.is_budget_exceeded("tenant-1") is False

    tracker.track(provider="openai", model="gpt-4o", prompt_tokens=1000000, completion_tokens=500000, tenant_id="tenant-1")
    assert tracker.get_spend("tenant-1") > 0


def test_cost_tracker_summary():
    tracker = CostTracker()
    tracker.track(provider="openai", model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50)
    tracker.track(provider="anthropic", model="claude-3-haiku", prompt_tokens=200, completion_tokens=100)

    summary = tracker.get_summary()
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == 450
    assert summary["success_rate"] == 100.0


def test_cost_tracker_summary_empty():
    tracker = CostTracker()
    summary = tracker.get_summary("nonexistent")
    assert summary["total_calls"] == 0


def test_cost_tracker_budget_exceeded():
    tracker = CostTracker()
    tracker.set_budget("tenant-2", 0.001)
    tracker.track(provider="openai", model="gpt-4o", prompt_tokens=500, completion_tokens=200, tenant_id="tenant-2")
    assert tracker.is_budget_exceeded("tenant-2") is True


# ── ProviderFactory Mock Integration ───────────────────────────────────────


@pytest.mark.asyncio
async def test_factory_mock_provider():
    ProviderFactory.register("mock_test", MockProvider)
    provider = ProviderFactory.create("mock_test")
    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "test"}]))
    assert "Mock response" in response.content


# ── ChatRequest defaults ──────────────────────────────────────────────────


def test_chat_request_defaults():
    req = ChatRequest()
    assert req.system is None
    assert req.messages is None
    assert req.stream is False
    assert req.metadata == {}


def test_chat_request_custom():
    req = ChatRequest(
        system="You are a helper",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.5,
        max_tokens=100,
        stream=True,
        tenant_id="t1",
    )
    assert req.system == "You are a helper"
    assert req.temperature == 0.5
    assert req.stream is True
    assert req.tenant_id == "t1"
