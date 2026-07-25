"""Tests for SearchCache — in-memory caching with TTL and hit tracking."""
from __future__ import annotations

import time

import pytest

from domains.search.caching.cache import SearchCache, SearchCacheStats
from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.contracts.repository import SearchRepository


# ── Fake Repository ─────────────────────────────────────────────────


class FakeSearchRepo(SearchRepository):
    """In-memory fake that tracks call count."""

    def __init__(self, results: list | None = None, total: int = 5):
        self._results = results or []
        self._total = total
        self.call_count = 0

    async def search(self, query: SearchQuery) -> SearchResult:
        self.call_count += 1
        return SearchResult(
            items=self._results,
            total=self._total,
            query=query.query,
        )

    async def count(self, query: SearchQuery) -> int:
        return self._total

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        return {}

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        return []


# ── Cache Hit / Miss ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_hit_on_second_call():
    repo = FakeSearchRepo(total=10)
    cache = SearchCache(repo, ttl_seconds=60)
    q = SearchQuery(query="test", tenant_id="t1")

    await cache.search(q)
    assert repo.call_count == 1

    await cache.search(q)
    assert repo.call_count == 1  # still 1 — cached

    assert cache.stats.hits == 1
    assert cache.stats.misses == 1


@pytest.mark.asyncio
async def test_cache_miss_for_different_queries():
    repo = FakeSearchRepo()
    cache = SearchCache(repo, ttl_seconds=60)

    await cache.search(SearchQuery(query="a", tenant_id="t1"))
    await cache.search(SearchQuery(query="b", tenant_id="t1"))
    assert repo.call_count == 2
    assert cache.stats.misses == 2


@pytest.mark.asyncio
async def test_cache_expiry():
    repo = FakeSearchRepo(total=5)
    cache = SearchCache(repo, ttl_seconds=0.01)  # 10ms TTL
    q = SearchQuery(query="expire", tenant_id="t1")

    await cache.search(q)
    assert repo.call_count == 1

    time.sleep(0.02)  # wait for expiry

    await cache.search(q)
    assert repo.call_count == 2  # expired — refetched


# ── Hit Rate ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hit_rate_calculation():
    repo = FakeSearchRepo()
    cache = SearchCache(repo, ttl_seconds=60)
    q = SearchQuery(query="rate", tenant_id="t1")

    await cache.search(q)  # miss
    await cache.search(q)  # hit
    await cache.search(q)  # hit

    assert cache.stats.hits == 2
    assert cache.stats.misses == 1
    assert abs(cache.stats.hit_rate - 2 / 3) < 1e-6


# ── Invalidation ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalidate_key():
    repo = FakeSearchRepo(total=1)
    cache = SearchCache(repo, ttl_seconds=60)
    q = SearchQuery(query="inv", tenant_id="t1")

    await cache.search(q)
    assert cache.get_entry_count() == 1

    await cache.invalidate_key(q)
    assert cache.get_entry_count() == 0

    await cache.search(q)
    assert repo.call_count == 2  # re-fetched


@pytest.mark.asyncio
async def test_clear_all():
    repo = FakeSearchRepo()
    cache = SearchCache(repo, ttl_seconds=60)

    for i in range(5):
        await cache.search(SearchQuery(query=f"q{i}", tenant_id="t1"))
    assert cache.get_entry_count() == 5

    await cache.clear()
    assert cache.get_entry_count() == 0


# ── Eviction ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_max_entries_eviction():
    repo = FakeSearchRepo()
    cache = SearchCache(repo, ttl_seconds=60, max_entries=3)

    for i in range(5):
        await cache.search(SearchQuery(query=f"q{i}", tenant_id="t1"))

    assert cache.get_entry_count() <= 3
    assert cache.stats.evictions > 0


# ── Stats ───────────────────────────────────────────────────────────


def test_stats_initial():
    stats = SearchCacheStats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.total == 0
    assert stats.hit_rate == 0.0


def test_stats_to_dict():
    stats = SearchCacheStats(hits=8, misses=2)
    d = stats.to_dict()
    assert d["hits"] == 8
    assert d["misses"] == 2
    assert d["total"] == 10
    assert d["hit_rate"] == 0.8


# ── Delegations ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_count_delegates():
    repo = FakeSearchRepo(total=42)
    cache = SearchCache(repo, ttl_seconds=60)
    c = await cache.count(SearchQuery(query="x"))
    assert c == 42


@pytest.mark.asyncio
async def test_facets_delegates():
    repo = FakeSearchRepo()
    cache = SearchCache(repo, ttl_seconds=60)
    f = await cache.facets(SearchQuery(query="x"), ["status"])
    assert f == {}


@pytest.mark.asyncio
async def test_suggest_delegates():
    repo = FakeSearchRepo()
    cache = SearchCache(repo, ttl_seconds=60)
    s = await cache.suggest(SearchQuery(query="x"), "name_ar", "comp")
    assert s == []
