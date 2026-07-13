"""Canonical cache module — re-exports from sdk.cache with URL-based factory."""

from __future__ import annotations

from typing import Any, Optional

import redis.asyncio as aioredis

from sdk.cache import CacheService as _SdkCacheService
from sdk.cache import cache_key

__all__ = ["CacheService", "cache_key", "create_cache_from_url"]


class CacheService(_SdkCacheService):
    """Backward-compatible CacheService that accepts a redis_url.

    Delegates all operations to the canonical sdk.cache.CacheService.
    """

    def __init__(self, redis_url: str, socket_connect_timeout: int = 2, socket_timeout: int = 2):
        redis = aioredis.Redis.from_url(
            redis_url,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
        )
        super().__init__(redis)
        self._redis_url = redis_url

    async def health(self) -> bool:
        try:
            return await self._redis.ping()
        except Exception:
            return False

    async def close(self):
        await self._redis.aclose()


async def create_cache_from_url(
    redis_url: str, socket_connect_timeout: int = 2, socket_timeout: int = 2
) -> CacheService:
    """Factory to create a CacheService from a Redis URL."""
    return CacheService(redis_url, socket_connect_timeout, socket_timeout)
