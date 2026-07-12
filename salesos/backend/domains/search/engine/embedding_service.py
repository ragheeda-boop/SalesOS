"""Embedding service adapter for the search domain.

Wraps the SDK OpenAIEmbeddingService with caching, fallback to local model,
and a clean async interface for the HybridSearchEngine.

Gracefully degrades: if OpenAI is unavailable, returns None instead of crashing.
"""

from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger(__name__)


class SearchEmbeddingService:
    """Embedding adapter for hybrid search.

    Features:
    - LRU-style in-memory cache (bounded by max_entries)
    - Graceful fallback: returns None on failure instead of raising
    - Batch embedding support for indexing
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        model: str = "text-embedding-3-large",
        max_cache_entries: int = 1024,
    ):
        self._api_key = openai_api_key
        self._model = model
        self._max_cache = max_cache_entries
        self._cache: dict[str, list[float]] = {}
        self._client = None

    @property
    def dimensions(self) -> int:
        """Return the embedding dimension for the configured model."""
        model_dims = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
            "all-MiniLM-L6-v2": 384,
        }
        return model_dims.get(self._model, 3072)

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _evict_if_needed(self) -> None:
        if len(self._cache) >= self._max_cache:
            # Remove oldest 25% of entries
            keys = list(self._cache.keys())
            for k in keys[: len(keys) // 4]:
                del self._cache[k]

    async def get_embedding(self, text: str) -> list[float] | None:
        """Get embedding for a single text. Returns None on failure."""
        if not text or not text.strip():
            return None

        key = self._cache_key(text)
        if key in self._cache:
            return self._cache[key]

        try:
            embedding = await self._call_api(text)
            if embedding:
                self._evict_if_needed()
                self._cache[key] = embedding
            return embedding
        except Exception as exc:
            logger.warning("Embedding failed (graceful fallback): %s", exc)
            return None

    async def get_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float] | None]:
        """Get embeddings for multiple texts. Returns list with None for failures."""
        if not texts:
            return []

        results: list[list[float] | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                continue
            key = self._cache_key(text)
            if key in self._cache:
                results[i] = self._cache[key]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if not uncached_texts:
            return results

        try:
            embeddings = await self._call_api_batch(uncached_texts)
            for idx, emb in zip(uncached_indices, embeddings, strict=True):
                if emb:
                    self._evict_if_needed()
                    self._cache[self._cache_key(texts[idx])] = emb
                results[idx] = emb
        except Exception as exc:
            logger.warning("Batch embedding failed (graceful fallback): %s", exc)

        return results

    async def _call_api(self, text: str) -> list[float] | None:
        """Call OpenAI embedding API for a single text."""
        try:
            import openai
        except ImportError:
            logger.warning("openai package not installed — semantic search disabled")
            return None

        if not self._api_key:
            logger.warning("No OpenAI API key — semantic search disabled")
            return None

        client = openai.AsyncOpenAI(api_key=self._api_key)
        response = await client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def _call_api_batch(
        self, texts: list[str]
    ) -> list[list[float] | None]:
        """Call OpenAI embedding API for a batch of texts."""
        try:
            import openai
        except ImportError:
            return [None] * len(texts)

        if not self._api_key:
            return [None] * len(texts)

        client = openai.AsyncOpenAI(api_key=self._api_key)

        # OpenAI batch limit is 2048 texts per request
        all_embeddings: list[list[float] | None] = []
        batch_size = 256

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = await client.embeddings.create(
                    model=self._model,
                    input=batch,
                )
                sorted_results = sorted(response.data, key=lambda x: x.index)
                all_embeddings.extend([r.embedding for r in sorted_results])
            except Exception:
                all_embeddings.extend([None] * len(batch))

        return all_embeddings
