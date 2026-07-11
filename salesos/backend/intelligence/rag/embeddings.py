from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from domains.rag.models import Document, DocumentChunk, EmbeddingConfig
from intelligence.rag.chunking import ChunkingService


class EmbeddingService:
    """Generates embeddings for text using OpenAI's embedding API.

    Caches embeddings by text hash to reduce API costs.
    Gracefully degrades if the API is unavailable.
    """

    def __init__(
        self,
        config: EmbeddingConfig | None = None,
        chunking_service: ChunkingService | None = None,
        openai_client: Any = None,
        max_retries: int = 3,
    ):
        self.config = config or EmbeddingConfig()
        self.chunking = chunking_service or ChunkingService()
        self._client = openai_client
        self._cache: dict[str, list[float]] = {}
        self._max_retries = max_retries

    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            from sdk.config import sdk_settings
            self._client = AsyncOpenAI(api_key=sdk_settings.openai_api_key)
        return self._client

    def _text_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def embed_text(self, text: str) -> list[float]:
        text_hash = self._text_hash(text)
        if text_hash in self._cache:
            return self._cache[text_hash]

        for attempt in range(self._max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.config.model_name,
                    input=text,
                )
                embedding = response.data[0].embedding
                self._cache[text_hash] = embedding
                return embedding
            except Exception as e:
                if attempt == self._max_retries - 1:
                    return []
                await asyncio.sleep(2 ** attempt)

        return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []
        results: list[list[float] | None] = [None] * len(texts)

        for i, text in enumerate(texts):
            text_hash = self._text_hash(text)
            if text_hash in self._cache:
                results[i] = self._cache[text_hash]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            batches = [
                uncached_texts[i : i + self.config.batch_size]
                for i in range(0, len(uncached_texts), self.config.batch_size)
            ]

            for batch_indices, batch_texts in zip(
                [uncached_indices[i : i + self.config.batch_size] for i in range(0, len(uncached_indices), self.config.batch_size)],
                batches,
            ):
                for attempt in range(self._max_retries):
                    try:
                        response = await self.client.embeddings.create(
                            model=self.config.model_name,
                            input=batch_texts,
                        )
                        sorted_results = sorted(response.data, key=lambda x: x.index)
                        for bi, emb in zip(batch_indices, sorted_results):
                            emb_list = emb.embedding
                            results[bi] = emb_list
                            self._cache[self._text_hash(texts[bi])] = emb_list
                        break
                    except Exception:
                        if attempt == self._max_retries - 1:
                            for bi in batch_indices:
                                results[bi] = []
                        await asyncio.sleep(2 ** attempt)

        return [r or [] for r in results]

    async def embed_document(
        self, document: Document, strategy: str = "hybrid"
    ) -> list[DocumentChunk]:
        chunks = self.chunking.chunk_document(document, strategy=strategy)
        texts = [c.content for c in chunks]
        embeddings = await self.embed_batch(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb
        return chunks
