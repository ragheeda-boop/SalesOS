from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .factory import ProviderFactory
from .protocol import LLMProvider


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class RoutingDecision:
    provider: str
    model: str
    complexity: ComplexityLevel
    reason: str
    estimated_cost: float = 0.0
    failover_chain: list[str] = field(default_factory=list)


class QueryRouter:
    """Routes LLM queries to the appropriate provider based on complexity and cost."""

    TIERS: dict[ComplexityLevel, dict[str, Any]] = {
        ComplexityLevel.SIMPLE: {
            "provider": "ollama",
            "model": "llama3.2",
            "fallback": "openai",
            "description": "Simple Q&A, classification, basic extraction",
        },
        ComplexityLevel.MODERATE: {
            "provider": "anthropic",
            "model": "claude-3-5-haiku-20241022",
            "fallback": "gemini",
            "description": "Analysis, summaries, content generation",
        },
        ComplexityLevel.COMPLEX: {
            "provider": "openai",
            "model": "gpt-4o",
            "fallback": "anthropic",
            "description": "Complex reasoning, high-stakes decisions, code generation",
        },
    }

    @classmethod
    def classify_complexity(
        cls,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
    ) -> ComplexityLevel:
        if tools:
            return ComplexityLevel.COMPLEX

        text = ""
        if system:
            text += system + " "
        if messages:
            for m in messages:
                text += m.get("content", "") + " "

        word_count = len(text.split())
        has_code = any(kw in text.lower() for kw in ["def ", "class ", "function", "code", "sql", "json"])
        has_reasoning = any(kw in text.lower() for kw in ["explain", "analyze", "compare", "evaluate", "why", "reason"])

        if word_count > 500 or has_code or (has_reasoning and word_count > 100):
            return ComplexityLevel.COMPLEX
        if word_count > 100 or has_reasoning:
            return ComplexityLevel.MODERATE
        return ComplexityLevel.SIMPLE

    @classmethod
    def route(
        cls,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        preferred_provider: str | None = None,
    ) -> RoutingDecision:
        complexity = cls.classify_complexity(system, messages, tools, max_tokens)

        if preferred_provider:
            tier = cls.TIERS.get(complexity, cls.TIERS[ComplexityLevel.SIMPLE])
            return RoutingDecision(
                provider=preferred_provider,
                model=tier.get("model", "gpt-4o-mini"),
                complexity=complexity,
                reason=f"User-preferred provider: {preferred_provider}",
                failover_chain=[p for p in ProviderFactory.FAILOVER_CHAIN if p != preferred_provider] + [preferred_provider],
            )

        tier = cls.TIERS.get(complexity, cls.TIERS[ComplexityLevel.SIMPLE])
        chain = [tier["provider"], tier["fallback"]]
        for p in ProviderFactory.FAILOVER_CHAIN:
            if p not in chain:
                chain.append(p)

        return RoutingDecision(
            provider=tier["provider"],
            model=tier["model"],
            complexity=complexity,
            reason=tier["description"],
            failover_chain=chain,
        )
