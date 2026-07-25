"""Tests for SearchAnalytics — query logging and aggregation."""
from __future__ import annotations

import time

import pytest

from domains.search.analytics.analytics import SearchAnalytics, SearchLogEntry
from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.contracts.repository import SearchRepository


# ── Fake Repository ─────────────────────────────────────────────────


class FakeAnalyticsRepo(SearchRepository):
    def __init__(self, total: int = 3):
        self._total = total

    async def search(self, query: SearchQuery) -> SearchResult:
        return SearchResult(items=[], total=self._total, query=query.query, strategy="postgres")

    async def count(self, query: SearchQuery) -> int:
        return self._total

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        return {}

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        return []


# ── Logging ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_logs_entry():
    repo = FakeAnalyticsRepo(total=5)
    analytics = SearchAnalytics(repo)
    result = await analytics.search(SearchQuery(query="test company", tenant_id="t1"))

    assert result.total == 5
    assert analytics.entry_count == 1
    entry = analytics.log_entries[0]
    assert entry.query == "test company"
    assert entry.result_count == 5
    assert entry.latency_ms >= 0


@pytest.mark.asyncio
async def test_multiple_searches_logged():
    repo = FakeAnalyticsRepo()
    analytics = SearchAnalytics(repo)

    await analytics.search(SearchQuery(query="a", tenant_id="t1"))
    await analytics.search(SearchQuery(query="b", tenant_id="t1"))
    await analytics.search(SearchQuery(query="a", tenant_id="t1"))

    assert analytics.entry_count == 3


# ── Top Queries ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_top_queries():
    repo = FakeAnalyticsRepo()
    analytics = SearchAnalytics(repo)

    for _ in range(5):
        await analytics.search(SearchQuery(query="popular", tenant_id="t1"))
    for _ in range(2):
        await analytics.search(SearchQuery(query="medium", tenant_id="t1"))
    await analytics.search(SearchQuery(query="rare", tenant_id="t1"))

    top = analytics.top_queries(n=2)
    assert len(top) == 2
    assert top[0]["query"] == "popular"
    assert top[0]["count"] == 5
    assert top[1]["query"] == "medium"
    assert top[1]["count"] == 2


@pytest.mark.asyncio
async def test_top_queries_excludes_empty():
    repo = FakeAnalyticsRepo()
    analytics = SearchAnalytics(repo)

    await analytics.search(SearchQuery(query="", tenant_id="t1"))
    await analytics.search(SearchQuery(query="real", tenant_id="t1"))

    top = analytics.top_queries(n=10)
    assert len(top) == 1
    assert top[0]["query"] == "real"


# ── Zero Result Queries ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_zero_result_queries():
    repo = FakeAnalyticsRepo(total=0)
    analytics = SearchAnalytics(repo)

    await analytics.search(SearchQuery(query="no match", tenant_id="t1"))
    await analytics.search(SearchQuery(query="also none", tenant_id="t1"))
    await analytics.search(SearchQuery(query="no match", tenant_id="t1"))

    zeros = analytics.zero_result_queries()
    assert len(zeros) == 2
    assert zeros[0]["query"] == "no match"
    assert zeros[0]["count"] == 2


@pytest.mark.asyncio
async def test_zero_result_queries_with_results():
    repo = FakeAnalyticsRepo(total=5)
    analytics = SearchAnalytics(repo)

    await analytics.search(SearchQuery(query="found", tenant_id="t1"))

    zeros = analytics.zero_result_queries()
    assert len(zeros) == 0


# ── Latency by Strategy ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_avg_latency_by_strategy():
    repo = FakeAnalyticsRepo()
    analytics = SearchAnalytics(repo)

    for _ in range(10):
        await analytics.search(SearchQuery(query="latency test", tenant_id="t1"))

    latency = analytics.avg_latency_by_strategy()
    assert "postgres" in latency
    assert latency["postgres"]["count"] == 10
    assert latency["postgres"]["avg_ms"] >= 0
    assert "p50_ms" in latency["postgres"]
    assert "p95_ms" in latency["postgres"]


# ── Volume Over Time ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_volume_over_time():
    repo = FakeAnalyticsRepo()
    analytics = SearchAnalytics(repo)

    for _ in range(3):
        await analytics.search(SearchQuery(query="volume", tenant_id="t1"))

    volume = analytics.volume_over_time(hours=1)
    assert len(volume) >= 1
    assert volume[0]["count"] == 3
    assert "hour" in volume[0]
    assert "avg_latency_ms" in volume[0]


# ── Summary ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_summary():
    repo = FakeAnalyticsRepo(total=0)
    analytics = SearchAnalytics(repo)

    await analytics.search(SearchQuery(query="summary test", tenant_id="t1"))

    s = analytics.summary()
    assert s["total_searches"] == 1
    assert s["zero_result_count"] == 1
    assert s["zero_result_rate"] == 1.0
    assert s["unique_queries"] == 1
    assert s["avg_latency_ms"] >= 0


# ── Clear ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clear():
    repo = FakeAnalyticsRepo()
    analytics = SearchAnalytics(repo)

    await analytics.search(SearchQuery(query="clear me", tenant_id="t1"))
    assert analytics.entry_count == 1

    analytics.clear()
    assert analytics.entry_count == 0


# ── Max Entries ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_max_entries_eviction():
    repo = FakeAnalyticsRepo()
    analytics = SearchAnalytics(repo, max_entries=3)

    for i in range(5):
        await analytics.search(SearchQuery(query=f"q{i}", tenant_id="t1"))

    assert analytics.entry_count == 3
    # oldest entries evicted
    entries = analytics.log_entries
    assert entries[0].query == "q2"


# ── SearchLogEntry ──────────────────────────────────────────────────


def test_log_entry_is_zero_result():
    entry = SearchLogEntry(query="x", filters={}, result_count=0, latency_ms=1.0, timestamp=time.time())
    assert entry.is_zero_result is True


def test_log_entry_is_not_zero_result():
    entry = SearchLogEntry(query="x", filters={}, result_count=5, latency_ms=1.0, timestamp=time.time())
    assert entry.is_zero_result is False


def test_log_entry_hour_bucket():
    entry = SearchLogEntry(query="x", filters={}, result_count=0, latency_ms=1.0, timestamp=1721126400.0)
    bucket = entry.hour_bucket
    assert "T" in bucket
    assert bucket.endswith("Z")
