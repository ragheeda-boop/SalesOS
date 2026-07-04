"""Embedding service for text vectorization."""

from abc import ABC, abstractmethod

from sdk.config import sdk_settings


class EmbeddingService(ABC):
    """Abstract embedding service for generating text vectors."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI-backed embedding service using text-embedding-3-large."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or sdk_settings.openai_api_key
        self._model = model or sdk_settings.openai_embedding_model

    async def embed(self, text: str) -> list[float]:
        import openai

        client = openai.AsyncOpenAI(api_key=self._api_key)
        response = await client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import openai

        client = openai.AsyncOpenAI(api_key=self._api_key)
        response = await client.embeddings.create(
            model=self._model,
            input=texts,
        )
        sorted_results = sorted(response.data, key=lambda x: x.index)
        return [r.embedding for r in sorted_results]
