"""STORY-06-04 residual — entitlement cache TTL / plan-downgrade soak."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.admin.entitlement_cache import (
    ENTITLEMENT_CACHE_TTL_MAX_SECONDS,
    EntitlementCache,
    clamp_entitlement_cache_ttl,
    reset_entitlement_cache_for_tests,
)
from app.modules.admin.entitlement_resolver import resolve_entitlements_for_tenant
from app.modules.admin.entitlements import (
    default_entitlements_for_tier,
    domain_enabled,
)


class _FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += float(seconds)


@pytest.fixture(autouse=True)
def _reset_cache_singleton():
    reset_entitlement_cache_for_tests(None)
    yield
    reset_entitlement_cache_for_tests(None)


def test_ttl_clamped_to_sixty_seconds_max() -> None:
    assert ENTITLEMENT_CACHE_TTL_MAX_SECONDS == 60
    assert clamp_entitlement_cache_ttl(60) == 60
    assert clamp_entitlement_cache_ttl(120) == 60
    assert clamp_entitlement_cache_ttl(0) == 1
    cache = EntitlementCache(ttl_seconds=999)
    assert cache.ttl_seconds == 60


@pytest.mark.asyncio
async def test_downgrade_invalidate_takes_effect_immediately() -> None:
    clock = _FakeClock()
    cache = EntitlementCache(ttl_seconds=60, redis_client=None, clock=clock)
    tid = "tenant-downgrade-a"
    await cache.set(tid, default_entitlements_for_tier("growth"), {"tier": "growth"})
    assert domain_enabled((await cache.get(tid))[0], "DOM-011") is True
    await cache.invalidate(tid)
    assert await cache.get(tid) is None
    await cache.set(tid, default_entitlements_for_tier("starter"), {"tier": "starter"})
    after = await cache.get(tid)
    assert after is not None
    assert domain_enabled(after[0], "DOM-011") is False


@pytest.mark.asyncio
async def test_ttl_soak_downgrade_without_manual_flush() -> None:
    clock = _FakeClock()
    ttl = 30
    cache = EntitlementCache(ttl_seconds=ttl, redis_client=None, clock=clock)
    tid = "tenant-soak-b"
    await cache.set(tid, default_entitlements_for_tier("growth"), {"tier": "growth"})
    clock.advance(ttl - 1)
    assert domain_enabled((await cache.get(tid))[0], "DOM-011") is True
    clock.advance(2)
    assert await cache.get(tid) is None
    await cache.set(tid, default_entitlements_for_tier("starter"), {"tier": "starter"})
    assert domain_enabled((await cache.get(tid))[0], "DOM-011") is False


@pytest.mark.asyncio
async def test_resolve_uses_cache_then_db_after_ttl() -> None:
    clock = _FakeClock()
    cache = EntitlementCache(ttl_seconds=10, redis_client=None, clock=clock)
    reset_entitlement_cache_for_tests(cache)
    tid = "11111111-1111-1111-1111-111111111111"
    resolve_db = AsyncMock(
        side_effect=[
            (
                default_entitlements_for_tier("growth"),
                {"tier": "growth", "plan_id": "p-g", "source": "admin_plans"},
            ),
            (
                default_entitlements_for_tier("starter"),
                {"tier": "starter", "plan_id": "p-s", "source": "admin_plans"},
            ),
        ]
    )
    with patch(
        "app.modules.admin.entitlement_resolver._resolve_entitlements_from_db",
        new=resolve_db,
    ):
        db = MagicMock()
        first, meta1 = await resolve_entitlements_for_tenant(db, tid)
        assert domain_enabled(first, "DOM-011") is True
        assert meta1.get("cache") == "miss"
        second, meta2 = await resolve_entitlements_for_tenant(db, tid)
        assert meta2.get("cache") == "memory_hit"
        assert resolve_db.await_count == 1
        clock.advance(11)
        third, meta3 = await resolve_entitlements_for_tenant(db, tid)
        assert domain_enabled(third, "DOM-011") is False
        assert meta3.get("tier") == "starter"
        assert resolve_db.await_count == 2


@pytest.mark.asyncio
async def test_resolve_skip_cache_always_hits_db() -> None:
    reset_entitlement_cache_for_tests(EntitlementCache(ttl_seconds=60, redis_client=None))
    resolve_db = AsyncMock(
        return_value=(
            default_entitlements_for_tier("starter"),
            {"tier": "starter", "source": "tier_default"},
        )
    )
    with patch(
        "app.modules.admin.entitlement_resolver._resolve_entitlements_from_db",
        new=resolve_db,
    ):
        db = MagicMock()
        await resolve_entitlements_for_tenant(db, "t", skip_cache=True)
        await resolve_entitlements_for_tenant(db, "t", skip_cache=True)
    assert resolve_db.await_count == 2


@pytest.mark.asyncio
async def test_redis_backend_roundtrip_and_invalidate() -> None:
    store: dict[str, tuple[str, int]] = {}

    class _FakeRedis:
        async def get(self, key: str) -> str | None:
            row = store.get(key)
            return row[0] if row else None

        async def set(self, key: str, value: str, ttl: int = 60) -> None:
            store[key] = (value, ttl)
            assert ttl <= 60

        async def delete(self, key: str) -> None:
            store.pop(key, None)

    clock = _FakeClock()
    r = _FakeRedis()
    writer = EntitlementCache(ttl_seconds=45, redis_client=r, clock=clock)
    reader = EntitlementCache(ttl_seconds=45, redis_client=r, clock=clock)
    await writer.set("tenant-redis", default_entitlements_for_tier("growth"), {"tier": "growth"})
    reader._memory.clear()
    hit = await reader.get("tenant-redis")
    assert hit is not None
    assert hit[1].get("cache") == "redis_hit"
    await writer.invalidate("tenant-redis")
    reader._memory.clear()
    assert await reader.get("tenant-redis") is None


def test_settings_default_ttl_is_sixty() -> None:
    from app.config import settings

    assert int(getattr(settings, "entitlement_cache_ttl_seconds", 0)) == 60
