from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


@dataclass
class ChatRequest:
    system: str | None = None
    messages: list[dict[str, str]] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    model: str | None = None
    stream: bool = False
    response_format: dict[str, Any] | None = None
    tools: list[dict[str, Any]] | None = None
    stop: list[str] | None = None
    tenant_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: FinishReason = FinishReason.STOP
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
    cost: float = 0.0


@dataclass
class StreamEvent:
    type: str  # "chunk" | "done" | "error" | "tool_call"
    content: str = ""
    finish_reason: FinishReason | None = None
    usage: dict[str, int] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass
class EmbeddingRequest:
    text: str | list[str]
    model: str | None = None


@dataclass
class EmbeddingResponse:
    embedding: list[float] | list[list[float]]
    model: str
    usage: dict[str, int] = field(default_factory=dict)


MODEL_COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.00025, "output": 0.00125},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
}

DEFAULT_COST = {"input": 0.001, "output": 0.002}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = MODEL_COST_PER_1K_TOKENS.get(model, DEFAULT_COST)
    input_cost = (prompt_tokens / 1000) * rates["input"]
    output_cost = (completion_tokens / 1000) * rates["output"]
    return round(input_cost + output_cost, 6)


def get_model_family(model: str) -> str:
    if model.startswith("gpt-"):
        return "openai"
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("gemini-"):
        return "gemini"
    if model.startswith("azure-") or "azure" in model.lower():
        return "azure"
    return "ollama"
