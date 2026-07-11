"""Tests for Redis caching layer — redis_client.py and cache.py."""
import os

# Must set before any app imports to satisfy settings validation
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test")

from unittest.mock import patch

import pytest

from app.common.cache import cached, make_cache_key


class FakeRedisClient:
    """In-memory mock that mirrors the AsyncRedisClient interface."""

    def __init__(self):
        self._store = {}
        self.available = True

    async def get(self, key: str) -> str | None:
        if not self.available:
            return None
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl: int = 60) -> None:
        if self.available:
            self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def health(self) -> bool:
        return self.available


@pytest.fixture
def fake_redis():
    return FakeRedisClient()


@pytest.fixture
def patch_redis_client(fake_redis):
    with patch("app.common.cache._cache_client", fake_redis) as mock:
        yield mock


# ── Tests: make_cache_key ────────────────────────────────────────────────────

class TestMakeCacheKey:
    def test_includes_tenant_and_resource(self):
        key = make_cache_key("t-1", "nba:recommendations", {"opportunity_id": "opp-1", "tenant_id": "t-1"})
        assert key.startswith("t-1:nba:recommendations:")

    def test_excludes_db_request(self):
        key_with = make_cache_key("t-1", "r", {"db": "x", "request": "y", "tenant_id": "t-1"})
        key_without = make_cache_key("t-1", "r", {"tenant_id": "t-1"})
        assert key_with == key_without

    def test_excludes_underscore_prefix(self):
        key_with = make_cache_key("t-1", "r", {"_rbac": None, "tenant_id": "t-1"})
        key_without = make_cache_key("t-1", "r", {"tenant_id": "t-1"})
        assert key_with == key_without

    def test_different_args_produce_different_keys(self):
        k1 = make_cache_key("t-1", "r", {"opportunity_id": "opp-1", "tenant_id": "t-1"})
        k2 = make_cache_key("t-1", "r", {"opportunity_id": "opp-2", "tenant_id": "t-1"})
        assert k1 != k2


# ── Tests: cached decorator ──────────────────────────────────────────────────

class TestCachedDecorator:
    async def test_returns_cached_value(self, patch_redis_client, fake_redis):
        call_count = 0

        @cached("test:resource", ttl=60)
        async def my_func(tenant_id: str, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"data": "expensive"}

        result1 = await my_func(tenant_id="t-1")
        assert result1 == {"data": "expensive"}
        assert call_count == 1

        result2 = await my_func(tenant_id="t-1")
        assert result2 == {"data": "expensive"}
        assert call_count == 1, "should use cache on second call"

    async def test_cache_miss_calls_function(self, patch_redis_client):
        call_count = 0

        @cached("test:resource", ttl=60)
        async def my_func(tenant_id: str, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"data": call_count}

        r1 = await my_func(tenant_id="t-1")
        r2 = await my_func(tenant_id="t-2")
        assert r1["data"] == 1
        assert r2["data"] == 2, "different tenant = different cache key"

    async def test_different_tenants_have_separate_cache(self, patch_redis_client):
        call_count = 0

        @cached("test:resource", ttl=60)
        async def my_func(tenant_id: str, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"data": call_count}

        await my_func(tenant_id="t-1")
        await my_func(tenant_id="t-2")
        await my_func(tenant_id="t-1")
        assert call_count == 2, "t-1 cached, t-2 miss"

    async def test_no_tenant_id_skips_cache(self, patch_redis_client, fake_redis):
        call_count = 0

        @cached("test:resource", ttl=60)
        async def my_func(**kwargs):
            nonlocal call_count
            call_count += 1
            return {"data": call_count}

        await my_func()
        await my_func()
        assert call_count == 2, "no tenant_id means no caching"

    async def test_graceful_degradation_when_redis_down(self):
        """When Redis is unavailable, the function should still execute."""
        redis_down = FakeRedisClient()
        redis_down.available = False

        call_count = 0

        with patch("app.common.cache._cache_client", redis_down):
            @cached("test:resource", ttl=60)
            async def my_func(tenant_id: str, **kwargs):
                nonlocal call_count
                call_count += 1
                return {"data": call_count}

            r1 = await my_func(tenant_id="t-1")
            r2 = await my_func(tenant_id="t-1")
            assert r1["data"] == 1
            assert r2["data"] == 2, "no cache when redis is down"
            assert call_count == 2


# ── Tests: FakeRedisClient (mock sanity) ────────────────────────────────────

class TestFakeRedisClient:
    async def test_get_set(self, fake_redis):
        await fake_redis.set("k", "v", ttl=10)
        assert await fake_redis.get("k") == "v"

    async def test_get_miss(self, fake_redis):
        assert await fake_redis.get("missing") is None

    async def test_delete(self, fake_redis):
        await fake_redis.set("k", "v")
        await fake_redis.delete("k")
        assert await fake_redis.get("k") is None

    async def test_health(self, fake_redis):
        assert await fake_redis.health() is True
        fake_redis.available = False
        assert await fake_redis.health() is False
