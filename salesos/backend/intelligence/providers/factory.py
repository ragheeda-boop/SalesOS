from __future__ import annotations

from typing import Any

from sdk.config import sdk_settings

from .base import LLMProvider
from .openai_provider import OpenAIProvider


class ProviderFactory:
    _providers: dict[str, type] = {
        "openai": OpenAIProvider,
    }

    @classmethod
    def register(cls, name: str, provider_cls: type):
        cls._providers[name] = provider_cls

    @classmethod
    def create(cls, provider_type: str = "openai", **kwargs) -> LLMProvider:
        provider_cls = cls._providers.get(provider_type)
        if not provider_cls:
            raise ValueError(f"Unknown provider type: {provider_type}. Available: {list(cls._providers.keys())}")
        return provider_cls(**kwargs)

    @classmethod
    def create_from_settings(cls, **overrides) -> LLMProvider:
        provider_type = overrides.pop("provider_type", "openai")
        kwargs = {
            "api_key": overrides.get("api_key") or sdk_settings.openai_api_key,
            "model": overrides.get("model") or sdk_settings.openai_model,
        }
        return cls.create(provider_type, **kwargs)


_default_provider: LLMProvider | None = None


def get_provider(**overrides) -> LLMProvider:
    global _default_provider
    if overrides:
        return ProviderFactory.create_from_settings(**overrides)
    if _default_provider is None:
        _default_provider = ProviderFactory.create_from_settings()
    return _default_provider
