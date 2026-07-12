"""AI Service — abstract provider interface, built-in providers, prompt-based generation."""
from __future__ import annotations

import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from domains.ai.models import PromptTemplate, AIModel
from domains.ai.evaluator import AIEvaluator

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        ...


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o") -> None:
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
            except ImportError:
                logger.warning("openai package not installed")
                self._client = None
        return self._client

    async def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        if not self.client:
            return ""
        try:
            response = await self.client.chat.completions.create(
                model=model or self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("OpenAI generation failed: %s", exc)
            return ""


class DecisionPlatformProvider(AIProvider):
    def __init__(self, decision_engine: Any = None) -> None:
        self._engine = decision_engine

    async def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        if not self._engine:
            return ""
        try:
            result = await self._engine.evaluate(prompt, kwargs.get("context", {}))
            if isinstance(result, dict):
                return result.get("explanation", result.get("reason", str(result)))
            return str(result)
        except Exception as exc:
            logger.error("Decision Platform generation failed: %s", exc)
            return ""


class AIService:
    def __init__(
        self,
        registry: Any | None = None,
        evaluator: AIEvaluator | None = None,
        providers: dict[str, AIProvider] | None = None,
    ) -> None:
        from domains.ai.registry import PromptRegistry
        self._registry = registry or PromptRegistry()
        self._evaluator = evaluator or AIEvaluator(self._registry)
        self._providers: dict[str, AIProvider] = providers or {}

    def register_provider(self, name: str, provider: AIProvider) -> None:
        self._providers[name] = provider

    async def generate(
        self,
        prompt_template_id: str,
        variables: dict[str, Any],
        provider: str = "openai",
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        template = self._registry.get(prompt_template_id)
        if not template:
            raise ValueError(f"Prompt template '{prompt_template_id}' not found")

        rendered = template.template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

        prov = self._providers.get(provider)
        if not prov:
            raise ValueError(f"AI provider '{provider}' not registered")

        return await prov.generate(rendered, model=model, **kwargs)

    async def explain(self, decision_id: str, context: dict[str, Any] | None = None) -> str:
        prov = self._providers.get("decision_platform")
        if not prov:
            return "Explainability unavailable — Decision Platform provider not registered"
        return await prov.generate(f"explain decision {decision_id}", context=context or {})
