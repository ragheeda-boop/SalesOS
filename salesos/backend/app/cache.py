import json
from typing import Any, Optional

import redis.asyncio as aioredis


class CacheService:
    def __init__(self, redis_url: str, socket_connect_timeout: int = 2, socket_timeout: int = 2):
        self.redis = aioredis.Redis.from_url(
            redis_url,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
        )

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def flush(self, pattern: str = "*"):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    async def set_many(self, mapping: dict[str, Any], ttl: int = 300):
        async with self.redis.pipeline() as pipe:
            for key, value in mapping.items():
                pipe.set(key, json.dumps(value), ex=ttl)
            await pipe.execute()

    async def get_many(self, keys: list[str]) -> dict[str, Optional[Any]]:
        data = await self.redis.mget(keys)
        return {
            key: json.loads(d) if d else None
            for key, d in zip(keys, data)
        }

    async def health(self) -> bool:
        try:
            return await self.redis.ping()
        except Exception:
            return False

    async def close(self):
        await self.redis.aclose()
