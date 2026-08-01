"""RedisCache — low-level async Redis wrapper with JSON serialisation, TTL, and graceful degradation."""  # noqa: E501

from __future__ import annotations

import json
import logging
from typing import Any, cast

from redis.asyncio import Redis  # type: ignore[import-untyped]
from redis.exceptions import RedisError  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis cache with JSON serialisation and graceful failover.

    All public methods catch RedisError internally so callers never need to
    handle them — when Redis is unavailable the cache behaves as an empty miss.
    """

    def __init__(self, redis: Redis | None = None) -> None:
        self._redis = redis

    @property
    def available(self) -> bool:
        return self._redis is not None

    async def get(self, key: str) -> Any | None:
        if self._redis is None:
            return None
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (RedisError, json.JSONDecodeError, TypeError) as exc:
            logger.warning("RedisCache GET %s failed: %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.setex(key, ttl, json.dumps(value, default=str))
        except (RedisError, TypeError) as exc:
            logger.warning("RedisCache SET %s failed: %s", key, exc)

    async def delete(self, key: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(key)
        except RedisError as exc:
            logger.warning("RedisCache DEL %s failed: %s", key, exc)

    async def exists(self, key: str) -> bool:
        if self._redis is None:
            return False
        try:
            return cast(bool, await self._redis.exists(key) > 0)
        except RedisError as exc:
            logger.warning("RedisCache EXISTS %s failed: %s", key, exc)
            return False

    async def clear(self) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.flushall()
        except RedisError as exc:
            logger.warning("RedisCache FLUSHALL failed: %s", exc)

    async def ttl(self, key: str) -> int:
        """Return remaining TTL in seconds.  -1 = no expiry, -2 = key missing."""
        if self._redis is None:
            return -2
        try:
            return cast(int, await self._redis.ttl(key))
        except RedisError as exc:
            logger.warning("RedisCache TTL %s failed: %s", key, exc)
            return -2

    async def scan_delete(self, pattern: str) -> int:
        """Delete all keys matching *pattern* and return the count."""
        if self._redis is None:
            return 0
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern)
                if keys:
                    deleted += await self._redis.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except RedisError as exc:
            logger.warning("RedisCache scan_delete %s failed: %s", pattern, exc)
            return 0
