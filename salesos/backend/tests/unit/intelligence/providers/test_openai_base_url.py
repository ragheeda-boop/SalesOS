"""OpenAI-compatible base_url shim — unit tests, no live network.

Wiring only. feature_ai_copilot remains False. No live LLM providers.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from intelligence.providers import OpenAIProvider, ProviderFactory
from intelligence.providers.base import ChatRequest, FinishReason
from intelligence.providers.factory import sdk_settings as factory_settings


def test_feature_ai_copilot_remains_false() -> None:
    assert settings.feature_ai_copilot is False


def test_sdk_openai_base_url_field_exists() -> None:
    assert hasattr(factory_settings, "openai_base_url")
    assert isinstance(factory_settings.openai_base_url, str)


def test_factory_passes_openai_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "http://freellmapi:3001/v1")
    monkeypatch.setattr(factory_settings, "openai_api_key", "sk-local-dev")
    provider = ProviderFactory.create_from_settings(provider_type="openai")
    assert isinstance(provider, OpenAIProvider)
    assert provider._base_url == "http://freellmapi:3001/v1"


def test_factory_openai_base_url_empty_becomes_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_settings, "openai_base_url", "")
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
