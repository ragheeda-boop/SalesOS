"""Embedding Cache — LRU cache with TTL for embedding vectors.

Target: >40% hit rate for repeated queries.
Cache key: text hash + model version
TTL: 24 hours
LRU eviction at 10K entries.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class EmbeddingCacheMetrics:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def snapshot(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "hit_rate": round(self.hit_rate, 4),
            "hit_rate_pct": f"{self.hit_rate * 100:.1f}%",
        }


class EmbeddingCache:
    """LRU cache for embedding vectors with TTL eviction.

    Args:
        max_entries: Maximum cache entries before LRU eviction (default 10K)
        ttl_seconds: Time-to-live in seconds (default 24h = 86400s)
    """

    def __init__(self, max_entries: int = 10_000, ttl_seconds: float = 86_400.0):
        self._max = max_entries
        self._ttl = ttl_seconds
        self._data: OrderedDict[str, tuple[float, list[float]]] = OrderedDict()
        self._lock = threading.Lock()
        self.metrics = EmbeddingCacheMetrics()

    @staticmethod
    def make_key(text: str, model_version: str) -> str:
        """Generate cache key from text content + model version."""
        raw = f"{model_version}:{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, text: str, model_version: str) -> Optional[list[float]]:
        """Retrieve cached embedding. Returns None on miss."""
        key = self.make_key(text, model_version)
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self.metrics.misses += 1
                return None
            ts, embedding = entry
            if time.monotonic() - ts > self._ttl:
                del self._data[key]
                self.metrics.misses += 1
                return None
            # Move to end (most recently used)
            self._data.move_to_end(key)
            self.metrics.hits += 1
            return embedding

    def put(self, text: str, model_version: str, embedding: list[float]) -> None:
        """Store embedding in cache with LRU eviction."""
        key = self.make_key(text, model_version)
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = (time.monotonic(), embedding)
            self.metrics.size = len(self._data)
            while len(self._data) > self._max:
                self._data.popitem(last=False)
                self.metrics.evictions += 1
                self.metrics.size = len(self._data)

    def get_or_compute(
        self,
        text: str,
        model_version: str,
        compute_fn: Any,
    ) -> list[float]:
        """Get from cache or compute and store.

        Args:
            text: Input text
            model_version: Model identifier
            compute_fn: Callable that returns list[float] embedding
        """
        cached = self.get(text, model_version)
        if cached is not None:
            return cached
        embedding = compute_fn(text)
        self.put(text, model_version, embedding)
        return embedding

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._data.clear()
            self.metrics = EmbeddingCacheMetrics()

    def invalidate(self, text: str, model_version: str) -> bool:
        """Invalidate a specific cache entry."""
        key = self.make_key(text, model_version)
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._data)
