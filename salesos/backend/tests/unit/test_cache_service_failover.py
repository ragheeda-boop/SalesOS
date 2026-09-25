"""CacheService must never turn a Redis outage into a caller-visible error.

Mechanical finding (project-audit/62): GET /api/v1/companies/{id} raised an
unhandled redis.exceptions.TimeoutError (a RedisError subclass) through
sdk.cache.CacheService.get() when Redis was unreachable, producing a 500
instead of a graceful cache miss. sdk.cache.redis_cache.RedisCache already
had this exact graceful-failover contract (and its own test suite); this
suite proves CacheService now matches it.
"""

from __future__ import annotations

import pytest
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from sdk.cache import CacheService


class FailingRedis:
    """Every call raises, like an unreachable Redis server would."""

    async def get(self, key: str):
        raise RedisTimeoutError("Timeout connecting to server")

    async def setex(self, key: str, ttl: int, value: str):
        raise RedisTimeoutError("Timeout connecting to server")

    async def delete(self, *keys: str):
        raise RedisTimeoutError("Timeout connecting to server")

    async def exists(self, key: str):
        raise RedisTimeoutError("Timeout connecting to server")

    async def flushall(self):
        raise RedisTimeoutError("Timeout connecting to server")

    async def scan(self, cursor: int = 0, match: str = "*"):
        raise RedisTimeoutError("Timeout connecting to server")


class WorkingRedis:
    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        self._store[key] = value

    async def delete(self, *keys: str):
        for k in keys:
            self._store.pop(k, None)

    async def exists(self, key: str):
        return 1 if key in self._store else 0

    async def flushall(self):
        self._store.clear()

    async def scan(self, cursor: int = 0, match: str = "*"):
        return 0, list(self._store)


@pytest.fixture
def failing_cache():
    return CacheService(FailingRedis())


@pytest.fixture
def working_cache():
    return CacheService(WorkingRedis())


class TestGracefulFailover:
    async def test_get_returns_none_on_redis_error(self, failing_cache):
        assert await failing_cache.get("k") is None

    async def test_set_does_not_raise_on_redis_error(self, failing_cache):
        await failing_cache.set("k", {"a": 1})

    async def test_delete_does_not_raise_on_redis_error(self, failing_cache):
        await failing_cache.delete("k")

    async def test_delete_pattern_does_not_raise_on_redis_error(self, failing_cache):
        await failing_cache.delete_pattern("prefix:*")

    async def test_exists_returns_false_on_redis_error(self, failing_cache):
        assert await failing_cache.exists("k") is False

    async def test_clear_all_does_not_raise_on_redis_error(self, failing_cache):
        await failing_cache.clear_all()

    async def test_remember_falls_through_to_factory_on_redis_error(self, failing_cache):
        called = {"n": 0}

        async def factory():
            called["n"] += 1
            return {"computed": True}

        result = await failing_cache.remember("k", 60, factory)
        assert result == {"computed": True}
        assert called["n"] == 1


class TestStillWorksWhenRedisIsUp:
    async def test_set_then_get_roundtrip(self, working_cache):
        await working_cache.set("k", {"a": 1})
        assert await working_cache.get("k") == {"a": 1}

    async def test_get_miss_returns_none(self, working_cache):
        assert await working_cache.get("missing") is None

    async def test_delete_removes_key(self, working_cache):
        await working_cache.set("k", "v")
        await working_cache.delete("k")
        assert await working_cache.get("k") is None

    async def test_exists_reflects_real_state(self, working_cache):
        await working_cache.set("k", "v")
        assert await working_cache.exists("k") is True
        assert await working_cache.exists("missing") is False


def test_redis_timeout_error_is_a_redis_error():
    # Guards the assumption this whole fix relies on: redis's TimeoutError
    # must be catchable via `except RedisError`, or the try/except in
    # CacheService silently stops working if the library ever changes this.
    assert issubclass(RedisTimeoutError, RedisError)
