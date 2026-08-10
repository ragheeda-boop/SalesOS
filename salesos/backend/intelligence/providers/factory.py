from __future__ import annotations

import logging
from typing import Any

from sdk.config import sdk_settings

from .base import ChatRequest, ChatResponse, FinishReason
from .protocol import LLMProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    _providers: dict[str, type] = {}

    FAILOVER_CHAIN: list[str] = ["openai", "anthropic", "gemini"]

    @classmethod
    def register(cls, name: str, provider_cls: type) -> None:
        cls._providers[name] = provider_cls

    @classmethod
    def create(cls, provider_type: str = "openai", **kwargs: Any) -> LLMProvider:
        provider_cls = cls._providers.get(provider_type)
        if not provider_cls:
            raise ValueError(f"Unknown provider type: {provider_type}. Available: {list(cls._providers.keys())}")
        return provider_cls(**kwargs)

    @classmethod
    def create_from_settings(cls, provider_type: str | None = None, **overrides: Any) -> LLMProvider:
        ptype = provider_type or overrides.pop("provider_type", None) or "openai"

        config_map = {
            "openai": lambda: {
                "api_key": overrides.get("api_key") or sdk_settings.openai_api_key,
                "model": overrides.get("model") or "gpt-4o-mini",
            },
            "anthropic": lambda: {
                "api_key": overrides.get("api_key") or sdk_settings.anthropic_api_key,
                "model": overrides.get("model") or "claude-3-5-sonnet-20241022",
            },
            "gemini": lambda: {
                "api_key": overrides.get("api_key") or sdk_settings.gemini_api_key,
                "model": overrides.get("model") or "gemini-1.5-flash",
            },
            "azure": lambda: {
                "api_key": overrides.get("api_key") or sdk_settings.azure_api_key,
                "azure_endpoint": overrides.get("azure_endpoint") or sdk_settings.azure_endpoint,
                "deployment": overrides.get("model") or "gpt-4o-mini",
            },
            "ollama": lambda: {
                "base_url": overrides.get("base_url") or "http://localhost:11434",
                "model": overrides.get("model") or "llama3.2",
            },
        }

        config_fn = config_map.get(ptype)
        if not config_fn:
            raise ValueError(f"No configuration for provider: {ptype}")

        return cls.create(ptype, **config_fn())

    @classmethod
    async def chat_with_failover(
        cls,
        request: ChatRequest,
        primary: str | None = None,
        chain: list[str] | None = None,
    ) -> ChatResponse:
        providers_to_try = chain or cls.FAILOVER_CHAIN
        if primary and primary in providers_to_try:
            providers_to_try = [primary] + [p for p in providers_to_try if p != primary]

        last_error = ""
        for provider_type in providers_to_try:
            try:
                provider = cls.create_from_settings(provider_type=provider_type)
                response = await provider.chat(request)
                if response.finish_reason != FinishReason.ERROR and response.content:
                    return response
                last_error = f"{provider_type}: empty response"
            except Exception as exc:
                last_error = f"{provider_type}: {exc}"
                logger.warning("Failover from %s: %s", provider_type, exc)
                continue

        return ChatResponse(
            content="",
            model="failover-exhausted",
            finish_reason=FinishReason.ERROR,
            usage={},
        )


_default_provider: LLMProvider | None = None


def get_provider(provider_type: str | None = None, **overrides: Any) -> LLMProvider:
    global _default_provider
    if provider_type or overrides:
        return ProviderFactory.create_from_settings(provider_type=provider_type, **overrides)
    if _default_provider is None:
        _default_provider = ProviderFactory.create_from_settings()
    return _default_provider
