"""OpenAI-compatible base_url shim — unit tests, no live network.

Wiring only. feature_ai_copilot remains False. No live LLM providers.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import Settings, settings
from domains.ai.service import OpenAIProvider as DomainOpenAIProvider
from domains.search.engine.embedding_service import SearchEmbeddingService
from intelligence.agents.llm import LLMService
from intelligence.providers import OpenAIProvider, ProviderFactory
from intelligence.providers.base import ChatRequest, FinishReason
from intelligence.providers.factory import sdk_settings as factory_settings
from intelligence.rag.embeddings import EmbeddingService
from sdk.config import resolve_openai_base_url
from sdk.vector import OpenAIEmbeddingService


def test_feature_ai_copilot_remains_false() -> None:
    assert settings.feature_ai_copilot is False


def test_sdk_openai_base_url_field_exists() -> None:
    assert hasattr(factory_settings, "openai_base_url")
    assert isinstance(factory_settings.openai_base_url, str)


def test_app_settings_openai_base_url_field_exists() -> None:
    assert hasattr(settings, "openai_base_url")
    assert isinstance(settings.openai_base_url, str)


def test_app_settings_openai_base_url_constructs() -> None:
    s = Settings(
        _env_file=None,
        secret_key="x" * 32,
        jwt_secret_key="y" * 32,
        openai_base_url="http://freellmapi:3001/v1",
    )
    assert s.openai_base_url == "http://freellmapi:3001/v1"
    assert s.feature_ai_copilot is False


def test_factory_passes_openai_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "http://freellmapi:3001/v1")
    monkeypatch.setattr(factory_settings, "openai_api_key", "sk-local-dev")
    provider = ProviderFactory.create_from_settings(provider_type="openai")
    assert isinstance(provider, OpenAIProvider)
    assert provider._base_url == "http://freellmapi:3001/v1"


def test_factory_openai_base_url_empty_becomes_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "")
    provider = ProviderFactory.create_from_settings(provider_type="openai", api_key="test-key")
    assert isinstance(provider, OpenAIProvider)
    assert provider._base_url is None


def test_factory_openai_base_url_override_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "http://from-settings:3001/v1")
    provider = ProviderFactory.create_from_settings(
        provider_type="openai",
        api_key="test-key",
        base_url="http://override:3001/v1",
    )
    assert provider._base_url == "http://override:3001/v1"


def test_factory_falls_back_to_app_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "http://freellmapi:3001/v1")
    provider = ProviderFactory.create_from_settings(provider_type="openai", api_key="test-key")
    assert isinstance(provider, OpenAIProvider)
    assert provider._base_url == "http://freellmapi:3001/v1"


def test_llm_service_inherits_app_openai_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "http://freellmapi:3001/v1")
    svc = LLMService(api_key="sk-local-dev")
    raw = svc._get_raw_provider()
    assert isinstance(raw, OpenAIProvider)
    assert raw._base_url == "http://freellmapi:3001/v1"


def test_llm_service_explicit_base_url_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "http://from-sdk:3001/v1")
    monkeypatch.setattr(settings, "openai_base_url", "http://from-app:3001/v1")
    svc = LLMService(api_key="sk-local-dev", base_url="http://override:3001/v1")
    raw = svc._get_raw_provider()
    assert raw._base_url == "http://override:3001/v1"


def test_rag_embeddings_inherits_app_openai_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(factory_settings, "openai_api_key", "sk-local-dev")
    monkeypatch.setattr(settings, "openai_base_url", "http://freellmapi:3001/v1")
    monkeypatch.setattr(settings, "openai_api_key", "sk-local-dev")
    svc = EmbeddingService()
    assert "freellmapi:3001/v1" in str(svc.client.base_url)


def test_resolve_openai_base_url_empty_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "")
    assert resolve_openai_base_url("") is None
    assert resolve_openai_base_url(None) is None


def test_sdk_vector_inherits_app_openai_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "http://freellmapi:3001/v1")
    svc = OpenAIEmbeddingService(api_key="sk-local-dev")
    assert svc._resolved_base_url() == "http://freellmapi:3001/v1"


def test_sdk_vector_openai_base_url_empty_becomes_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "")
    svc = OpenAIEmbeddingService(api_key="sk-local-dev")
    assert svc._resolved_base_url() is None


def test_sdk_vector_explicit_base_url_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "http://from-sdk:3001/v1")
    monkeypatch.setattr(settings, "openai_base_url", "http://from-app:3001/v1")
    svc = OpenAIEmbeddingService(api_key="sk-local-dev", base_url="http://override:3001/v1")
    assert svc._resolved_base_url() == "http://override:3001/v1"


def test_search_embeddings_inherits_app_openai_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "http://freellmapi:3001/v1")
    svc = SearchEmbeddingService(openai_api_key="sk-local-dev")
    assert svc._resolved_base_url() == "http://freellmapi:3001/v1"


def test_search_embeddings_openai_base_url_empty_becomes_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "")
    svc = SearchEmbeddingService(openai_api_key="sk-local-dev")
    assert svc._resolved_base_url() is None


def test_domain_ai_provider_inherits_app_openai_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "openai_base_url", "http://freellmapi:3001/v1")
    provider = DomainOpenAIProvider(api_key="sk-local-dev")
    assert "freellmapi:3001/v1" in str(provider.client.base_url)


def test_domain_ai_provider_no_key_stays_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_base_url", "http://freellmapi:3001/v1")
    provider = DomainOpenAIProvider(api_key=None)
    assert provider.client is None


@pytest.mark.asyncio
async def test_openai_compatible_chat_mocked_no_network() -> None:
    """Mock OpenAI-compatible client. Must not open sockets."""
    provider = OpenAIProvider(api_key="sk-local", base_url="http://127.0.0.1:9/v1")
    mock_choice = MagicMock()
    mock_choice.message.content = "hello from shim"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 1
    mock_usage.completion_tokens = 2
    mock_usage.total_tokens = 3
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    mock_response.model = "local-shim-model"

    provider._client = AsyncMock()
    provider._client.chat.completions.create = AsyncMock(return_value=mock_response)

    response = await provider.chat(ChatRequest(messages=[{"role": "user", "content": "hi"}]))
    assert response.content == "hello from shim"
    assert response.model == "local-shim-model"
    assert response.finish_reason == FinishReason.STOP
    provider._client.chat.completions.create.assert_awaited_once()
