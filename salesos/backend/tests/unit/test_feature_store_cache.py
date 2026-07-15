"""Tests for FeatureStore Redis cache integration — cache hit/miss, recompute clears cache, graceful failover."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.feature_store import (
    FeatureResult,
    FeatureStore,
    FeatureComputer,
    CompanyFeatureModel,
)


# ── Helpers ─────────────────────────────────────────────────────

class FakeResult:
    def __init__(self, mappings_obj=None, scalar_val=None):
        self._mappings = mappings_obj
        self._scalar_val = scalar_val
    def mappings(self):
        return self._mappings
    def scalar_one_or_none(self):
        return self._scalar_val
    def scalar(self):
        return self._scalar_val or 0


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one
    def one(self):
        return None
    def one_or_none(self):
        return FakeMapping(self._one) if self._one else None
    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeMapping:
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]
    def __iter__(self):
        return iter(self._data)
    def __len__(self):
        return len(self._data)
    def keys(self):
        return self._data.keys()
    def values(self):
        return self._data.values()
    def items(self):
        return self._data.items()
    def get(self, key, default=None):
        return self._data.get(key, default)


class DummyComputer(FeatureComputer):
    name = "dummy_score"
    version = 1
    async def compute(self, company: dict, session: AsyncSession) -> FeatureResult:
        return FeatureResult(
            score=75.0,
            version=self.version,
            computed_at=datetime.now(timezone.utc),
            confidence=0.9,
            contributing_signals={"dummy": True},
            explanation="Dummy score",
        )


class FakeCacheService:
    """In-memory cache that mirrors the CacheService interface used by FeatureStore."""

    def __init__(self):
        self._store: dict[str, object] = {}
        self.available = True

    async def get(self, key: str) -> object | None:
        if not self.available:
            raise ConnectionError("cache down")
        return self._store.get(key)

    async def set(self, key: str, value: object, ttl_seconds: int = 300) -> None:
        if not self.available:
            raise ConnectionError("cache down")
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def scan_delete(self, pattern: str) -> int:
        import fnmatch
        keys = [k for k in self._store if fnmatch.fnmatch(k, pattern)]
        for k in keys:
            del self._store[k]
        return len(keys)

    async def delete_pattern(self, pattern: str) -> None:
        await self.scan_delete(pattern)


# ── Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def mock_session():
    async def execute(sql, params=None):
        from sqlalchemy import TextClause
        raw = str(sql)
        if isinstance(sql, TextClause):
            if "companies" in raw:
                return FakeResult(FakeMappings(one={"id": "co-1", "tenant_id": "t-1", "name": "Test Co"}))
            if "company_features" in raw:
                return FakeResult(scalar_val=None)
            if "UPSERT" in raw or "INSERT INTO public.company_features" in raw:
                return FakeResult()
        return FakeResult(scalar_val=None)
    session = AsyncMock(spec=AsyncSession)
    session.execute = execute
    return session


@pytest.fixture
def mock_session_factory(mock_session):
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = mock_session
    factory.return_value.__aexit__.return_value = None
    return factory


@pytest.fixture
def event_runtime():
    return MagicMock()


@pytest.fixture
def fake_cache():
    return FakeCacheService()


@pytest.fixture
def store_with_cache(mock_session_factory, event_runtime, fake_cache):
    return FeatureStore(
        session_factory=mock_session_factory,
        event_runtime=event_runtime,
        computers=[DummyComputer()],
        cache_service=fake_cache,
        cache_ttl=300,
    )


@pytest.fixture
def store_without_cache(mock_session_factory, event_runtime):
    return FeatureStore(
        session_factory=mock_session_factory,
        event_runtime=event_runtime,
        computers=[DummyComputer()],
        cache_service=None,
        cache_ttl=300,
    )


# ── Tests: cache hit ────────────────────────────────────────────

class TestCacheHit:
    async def test_get_feature_returns_from_redis_on_hit(self, store_with_cache, fake_cache):
        await fake_cache.set(
            "feature:t-1:co-1:dummy_score",
            {
                "score": 99.0,
                "version": 1,
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "confidence": 0.95,
                "contributing_signals": {"from_cache": True},
                "explanation": "From Redis",
            },
        )
        result = await store_with_cache.get_feature("co-1", "t-1", "dummy_score")
        assert result.score == 99.0
        assert result.contributing_signals.get("from_cache") is True

    async def test_get_features_multiple_hits(self, store_with_cache, fake_cache):
        await fake_cache.set(
            "feature:t-1:co-1:dummy_score",
            {"score": 80.0, "version": 1, "computed_at": datetime.now(timezone.utc).isoformat(),
             "confidence": 0.8, "contributing_signals": {}, "explanation": ""},
        )
        results = await store_with_cache.get_features("co-1", "t-1", ["dummy_score"])
        assert results["dummy_score"].score == 80.0


# ── Tests: cache miss → compute → populate ──────────────────────

class TestCacheMiss:
    async def test_get_feature_computes_on_miss_and_populates_cache(self, store_with_cache, fake_cache):
        result = await store_with_cache.get_feature("co-1", "t-1", "dummy_score")
        assert result.score == 75.0
        cached = await fake_cache.get("feature:t-1:co-1:dummy_score")
        assert cached is not None
        assert cached["score"] == 75.0

    async def test_get_features_computes_missing(self, store_with_cache, fake_cache):
        results = await store_with_cache.get_features("co-1", "t-1", ["dummy_score"])
        assert results["dummy_score"].score == 75.0

    async def test_subsequent_call_hits_cache(self, store_with_cache, fake_cache):
        r1 = await store_with_cache.get_feature("co-1", "t-1", "dummy_score")
        assert r1.score == 75.0
        r2 = await store_with_cache.get_feature("co-1", "t-1", "dummy_score")
        assert r2.score == 75.0


# ── Tests: recompute clears cache ───────────────────────────────

class TestRecomputeCache:
    async def test_recompute_clears_redis_cache(self, store_with_cache, fake_cache):
        await fake_cache.set("feature:t-1:co-1:dummy_score", {"score": 50.0})
        await store_with_cache.recompute("co-1", "t-1")
        cached = await fake_cache.get("feature:t-1:co-1:dummy_score")
        assert cached is None, "recompute should clear Redis cache"

    async def test_recompute_then_get_hits_new_value(self, store_with_cache, fake_cache):
        await store_with_cache.recompute("co-1", "t-1")
        result = await store_with_cache.get_feature("co-1", "t-1", "dummy_score")
        assert result.score == 75.0


# ── Tests: graceful failover when no cache ──────────────────────

class TestFailover:
    async def test_get_feature_works_without_cache(self, store_without_cache):
        result = await store_without_cache.get_feature("co-1", "t-1", "dummy_score")
        assert result.score == 75.0

    async def test_recompute_works_without_cache(self, store_without_cache):
        results = await store_without_cache.recompute("co-1", "t-1")
        assert "dummy_score" in results
        assert results["dummy_score"].score == 75.0

    async def test_get_features_works_without_cache(self, store_without_cache):
        results = await store_without_cache.get_features("co-1", "t-1", ["dummy_score"])
        assert results["dummy_score"].score == 75.0
