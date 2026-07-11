"""Async Redis client with graceful degradation — singleton pattern."""
import logging
from typing import Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)


class AsyncRedisClient:
    _instance: Optional["AsyncRedisClient"] = None

    def __new__(cls) -> "AsyncRedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._redis: Optional[Redis] = None
        self._connect()

    def _connect(self) -> None:
        try:
            self._redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            logger.info("Redis client connected to %s", settings.redis_url)
        except Exception as exc:
            logger.warning("Redis unavailable at %s: %s — running without cache", settings.redis_url, exc)

    async def get(self, key: str) -> Optional[str]:
        if self._redis is None:
            return None
        try:
            return await self._redis.get(key)
        except RedisError as exc:
            logger.warning("Redis GET %s failed: %s", key, exc)
            return None

    async def set(self, key: str, value: str, ttl: int = 60) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.setex(key, ttl, value)
        except RedisError as exc:
            logger.warning("Redis SET %s failed: %s", key, exc)

    async def delete(self, key: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(key)
        except RedisError as exc:
            logger.warning("Redis DEL %s failed: %s", key, exc)

    async def health(self) -> bool:
        if self._redis is None:
            return False
        try:
            await self._redis.ping()
            return True
        except RedisError:
            return False
