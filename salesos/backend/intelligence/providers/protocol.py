from __future__ import annotations

from typing import AsyncIterator, Protocol

from .base import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, StreamEvent


class LLMProvider(Protocol):
    async def chat(self, request: ChatRequest) -> ChatResponse:
        ...

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        ...

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...

    @property
    def model_name(self) -> str:
        ...

    @property
    def provider_name(self) -> str:
        ...
