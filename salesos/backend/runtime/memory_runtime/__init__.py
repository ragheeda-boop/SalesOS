"""Memory Runtime — bounded in-memory store with TTL and LRU eviction."""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_DEFAULT_MAX_ENTRIES = 10000
_DEFAULT_TTL_SECONDS = 3600


class BoundedStore(Generic[T]):
    """TLL + LRU bounded in-memory key-value store.

    Enforces max size with LRU eviction and time-based TTL expiration.
    Writes a warning log whenever eviction occurs.
    """

    def __init__(
        self,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ):
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, tuple[float, T]] = OrderedDict()

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self._ttl_seconds:
            del self._store[key]
            logger.warning("BoundedStore: key=%s evicted (TTL expired)", key)
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: T) -> None:
        self._evict()
        self._store[key] = (time.monotonic(), value)
        self._store.move_to_end(key)

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def size(self) -> int:
        self._sweep_expired()
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()

    def keys(self) -> list[str]:
        self._sweep_expired()
        return list(self._store.keys())

    def _evict(self) -> int:
        evicted = 0
        self._sweep_expired()
        overflow = len(self._store) - self._max_entries
        while overflow > 0:
            oldest_key, _ = self._store.popitem(last=False)
            evicted += 1
            overflow -= 1
            logger.warning("BoundedStore: key=%s evicted (LRU overflow)", oldest_key)
        return evicted

    def _sweep_expired(self) -> int:
        now = time.monotonic()
        expired = [k for k, (ts, _) in self._store.items() if now - ts > self._ttl_seconds]
        for k in expired:
            del self._store[k]
        if expired:
            logger.warning("BoundedStore: %d keys evicted (TTL sweep)", len(expired))
        return len(expired)


class MemoryRuntime:
    """Memory runtime providing bounded stores with TTL + LRU eviction.

    Replaces unbounded dict/list patterns across the platform.
    """

    def __init__(
        self,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ):
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._stores: dict[str, BoundedStore[Any]] = {}

    def store(self, name: str) -> BoundedStore[Any]:
        if name not in self._stores:
            self._stores[name] = BoundedStore(
                max_entries=self._max_entries,
                ttl_seconds=self._ttl_seconds,
            )
        return self._stores[name]

    def metrics(self) -> dict:
        return {
            "stores": len(self._stores),
            "total_entries": sum(s.size() for s in self._stores.values()),
        }
