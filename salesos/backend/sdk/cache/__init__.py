"""Cache abstraction backed by Redis."""

import json
import logging
from collections.abc import Callable
from typing import Any, cast

from redis.asyncio import Redis  # type: ignore[import-untyped]
from redis.exceptions import RedisError  # type: ignore[import-untyped]

from sdk.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class CacheService:
    """High-level cache service with typed get/set and TTL support.

    All modules use this service instead of talking to Redis directly.
    A look-aside cache must never turn a Redis outage into a request
    failure — every method here catches Redis/serialization errors and
    degrades to a safe default (empty miss / silent no-op), matching
    sdk.cache.redis_cache.RedisCache's established graceful-failover
    contract.
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get(self, key: str) -> Any | None:
        try:
            value = await self._redis.get(key)
        except RedisError as exc:
            logger.warning("CacheService GET %s failed: %s", key, exc)
            return None
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("CacheService GET %s decode failed: %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        try:
            await self._redis.setex(key, ttl_seconds, json.dumps(value, default=str))
        except (RedisError, TypeError) as exc:
            logger.warning("CacheService SET %s failed: %s", key, exc)

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except RedisError as exc:
            logger.warning("CacheService DELETE %s failed: %s", key, exc)

    async def delete_pattern(self, pattern: str) -> None:
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
        except RedisError as exc:
            logger.warning("CacheService delete_pattern %s failed: %s", pattern, exc)

    async def remember(self, key: str, ttl_seconds: int, factory: Callable[[], Any]) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl_seconds)
        return value

    async def exists(self, key: str) -> bool:
        try:
            return cast(bool, await self._redis.exists(key) > 0)
        except RedisError as exc:
            logger.warning("CacheService EXISTS %s failed: %s", key, exc)
            return False

    async def clear_all(self) -> None:
        try:
            await self._redis.flushall()
        except RedisError as exc:
            logger.warning("CacheService clear_all failed: %s", exc)

    def _build_key(self, prefix: str, *parts: str) -> str:
        return ":".join([prefix] + list(parts))


def cache_key(prefix: str, *parts: str) -> str:
    """Build a colon-delimited cache key."""
    return ":".join([prefix] + list(parts))


__all__ = [
    "CacheService",
    "RedisCache",
    "cache_key",
]
