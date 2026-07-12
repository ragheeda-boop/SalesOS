from __future__ import annotations

from openai import AsyncOpenAI

from .base import LLMProvider, ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse


class OpenAIProvider:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.default_model = model

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self._client:
            return ChatResponse(content="", model=self.default_model, finish_reason="error")

        msgs = []
        if request.system:
            msgs.append({"role": "system", "content": request.system})
        if request.messages:
            msgs.extend(request.messages)

        response = await self._client.chat.completions.create(
            model=request.model or self.default_model,
            messages=msgs,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason or "stop",
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        if not self._client:
            return EmbeddingResponse(embedding=[], model=request.model or "text-embedding-3-large")
        model = request.model or "text-embedding-3-large"
        response = await self._client.embeddings.create(model=model, input=request.text)
        data = response.data[0]
        return EmbeddingResponse(
            embedding=data.embedding,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
        )
