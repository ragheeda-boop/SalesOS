"""Cache abstraction backed by Redis."""

import json
from typing import Any, Callable

from redis.asyncio import Redis


class CacheService:
    """High-level cache service with typed get/set and TTL support.

    All modules use this service instead of talking to Redis directly.
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get(self, key: str) -> Any | None:
        value = await self._redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await self._redis.setex(key, ttl_seconds, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(cursor, match=pattern)
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break

    async def remember(
        self, key: str, ttl_seconds: int, factory: Callable[[], Any]
    ) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl_seconds)
        return value

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key) > 0

    async def clear_all(self) -> None:
        await self._redis.flushall()

    def _build_key(self, prefix: str, *parts: str) -> str:
        return ":".join([prefix] + list(parts))


def cache_key(prefix: str, *parts: str) -> str:
    """Build a colon-delimited cache key."""
    return ":".join([prefix] + list(parts))
