"""LLM service abstraction for AI agents."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"


class LLMService:
    """Minimal LLM interface. Currently supports OpenAI.

    Swap implementation to switch provider (Anthropic, Gemini, etc.)
    without changing agent code.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        return self._client

    async def chat(
        self,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.client:
            return LLMResponse(content="", model=self.model, finish_reason="error")

        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        if messages:
            msgs.extend(messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason or "stop",
        )

    async def embed(self, text: str, model: str = "text-embedding-3-large") -> list[float]:
        if not self.client:
            return []
        response = await self.client.embeddings.create(model=model, input=text)
        return response.data[0].embedding
