from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ChatRequest:
    system: str | None = None
    messages: list[dict[str, str]] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    model: str | None = None


@dataclass
class ChatResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"


@dataclass
class EmbeddingRequest:
    text: str
    model: str | None = None


@dataclass
class EmbeddingResponse:
    embedding: list[float]
    model: str
    usage: dict[str, int] = field(default_factory=dict)


class LLMProvider(Protocol):
    async def chat(self, request: ChatRequest) -> ChatResponse:
        ...

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...
