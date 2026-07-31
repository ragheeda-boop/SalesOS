"""Tests for RedisCache — async Redis wrapper with JSON serialisation and graceful failover."""

from __future__ import annotations

import pytest

from sdk.cache.redis_cache import RedisCache


class FakeStubRedis:
    """Minimal Redis mock that stores JSON-serialised strings."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self.available = True

    async def get(self, key: str) -> str | None:
        if not self.available:
            raise ConnectionError("Redis unavailable")
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        if not self.available:
            raise ConnectionError("Redis unavailable")
        self._store[key] = value

    async def delete(self, *keys: str) -> int:
        if not self.available:
            raise ConnectionError("Redis unavailable")
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
        return count

    async def exists(self, key: str) -> int:
        if not self.available:
            raise ConnectionError("Redis unavailable")
        return 1 if key in self._store else 0

    async def ttl(self, key: str) -> int:
        if not self.available:
            raise ConnectionError("Redis unavailable")
        return 120 if key in self._store else -2

    async def flushall(self) -> None:
        if not self.available:
            raise ConnectionError("Redis unavailable")
        self._store.clear()

    async def scan(self, cursor: int = 0, match: str = "*", count: int = 10):
        if not self.available:
            raise ConnectionError("Redis unavailable")
        keys = [k for k in self._store if self._match_pattern(k, match)]
        return 0, keys

    @staticmethod
    def _match_pattern(key: str, pattern: str) -> bool:
        import fnmatch

        return fnmatch.fnmatch(key, pattern)


@pytest.fixture
def stub_redis():
    return FakeStubRedis()


@pytest.fixture
def cache(stub_redis):
    return RedisCache(stub_redis)


# ── Construction / availability ─────────────────────────────────


class TestConstruction:
    def test_with_none_redis(self):
        c = RedisCache(None)
        assert c.available is False

    def test_with_redis(self, stub_redis):
        c = RedisCache(stub_redis)
        assert c.available is True


# ── get / set ───────────────────────────────────────────────────


class TestGetSet:
    async def test_set_and_get(self, cache, stub_redis):
        await cache.set("k1", {"a": 1}, ttl=60)
        val = await cache.get("k1")
        assert val == {"a": 1}

    async def test_get_miss_returns_none(self, cache):
        val = await cache.get("nonexistent")
        assert val is None

    async def test_get_empty_string(self, cache):
        await cache.set("empty", "", ttl=60)
        val = await cache.get("empty")
        assert val == ""

    async def test_set_overwrites(self, cache):
        await cache.set("k", "v1", ttl=60)
        await cache.set("k", "v2", ttl=60)
        assert await cache.get("k") == "v2"


# ── delete ──────────────────────────────────────────────────────


class TestDelete:
    async def test_delete_existing(self, cache):
        await cache.set("k", "v", ttl=60)
        await cache.delete("k")
        assert await cache.get("k") is None

    async def test_delete_missing_does_not_raise(self, cache):
        await cache.delete("nonexistent")


# ── ttl ─────────────────────────────────────────────────────────


class TestTtl:
    async def test_ttl_returns_positive_for_existing(self, cache, stub_redis):
        await cache.set("k", "v", ttl=120)
        remaining = await cache.ttl("k")
        assert remaining > 0

    async def test_ttl_returns_minus2_for_missing(self, cache):
        assert await cache.ttl("nonexistent") == -2


# ── exists ──────────────────────────────────────────────────────


class TestExists:
    async def test_exists_returns_true(self, cache):
        await cache.set("k", "v", ttl=60)
        assert await cache.exists("k") is True

    async def test_exists_returns_false(self, cache):
        assert await cache.exists("missing") is False


# ── clear ───────────────────────────────────────────────────────


class TestClear:
    async def test_clear_empties_cache(self, cache):
        await cache.set("a", 1, ttl=60)
        await cache.set("b", 2, ttl=60)
        await cache.clear()
        assert await cache.get("a") is None
        assert await cache.get("b") is None


# ── Graceful failover ───────────────────────────────────────────


class TestFailover:
    async def test_get_returns_none_when_redis_unavailable(self):
        c = RedisCache(None)
        assert await c.get("any") is None

    async def test_set_does_not_raise_when_redis_down(self):
        c = RedisCache(None)
        await c.set("k", "v", ttl=60)

    async def test_delete_does_not_raise_when_redis_down(self):
        c = RedisCache(None)
        await c.delete("k")

    async def test_exists_returns_false_when_redis_down(self):
        c = RedisCache(None)
        assert await c.exists("k") is False

    async def test_clear_does_not_raise_when_redis_down(self):
        c = RedisCache(None)
        await c.clear()

    async def test_scan_delete_returns_zero_when_redis_down(self):
        c = RedisCache(None)
        assert await c.scan_delete("*") == 0
