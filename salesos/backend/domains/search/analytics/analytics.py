"""SearchAnalytics — query logging, aggregation, and reporting.

Logs every search query with metadata and provides aggregation endpoints:
  - Top N queries by frequency
  - Zero-result queries
  - Average latency per query type
  - Search volume over time (hourly buckets)

Architecture:
  - In-memory ring buffer (no external dependencies)
  - Thread-safe for concurrent search requests
  - Wraps any SearchRepository transparently
  - Stats reset on restart (production would persist to DB)
"""

from __future__ import annotations

import logging
import time
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import SearchQuery, SearchResult
from ..contracts.repository import SearchRepository

logger = logging.getLogger(__name__)

DEFAULT_MAX_ENTRIES = 10_000


@dataclass
class SearchLogEntry:
    """A single search log record."""

    query: str
    filters: dict[str, Any]
    result_count: int
    latency_ms: float
    timestamp: float
    tenant_id: str = ""
    strategy: str = ""
    page_size: int = 20

    @property
    def is_zero_result(self) -> bool:
        return self.result_count == 0

    @property
    def hour_bucket(self) -> str:
        """Return an ISO-format hour bucket for time-series aggregation."""
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:00:00Z")


class SearchAnalytics:
    """Analytics layer wrapping a SearchRepository.

    Logs every search call and provides aggregation queries for dashboards.

    Usage:
        repo = PostgresSearchRepository(session_factory)
        analytics = SearchAnalytics(repo, max_entries=10000)
        result = await analytics.search(query)
        top = analytics.top_queries(n=10)
        zeros = analytics.zero_result_queries()
        latency = analytics.avg_latency_by_strategy()
        volume = analytics.volume_over_time(hours=24)
    """

    def __init__(
        self,
        repository: SearchRepository,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        self._repository = repository
        self._max_entries = max_entries
        self._log: list[SearchLogEntry] = []
        self._lock = threading.Lock()

    @property
    def log_entries(self) -> list[SearchLogEntry]:
        """Return a snapshot of all log entries."""
        with self._lock:
            return list(self._log)

    @property
    def entry_count(self) -> int:
        with self._lock:
            return len(self._log)

    def _record(self, entry: SearchLogEntry) -> None:
        """Add a log entry, evicting oldest if over capacity."""
        with self._lock:
            if len(self._log) >= self._max_entries:
                self._log.pop(0)
            self._log.append(entry)

    async def search(self, query: SearchQuery) -> SearchResult:
        """Execute search and log the result."""
        t0 = time.monotonic()
        result = await self._repository.search(query)
        latency_ms = (time.monotonic() - t0) * 1000

        entry = SearchLogEntry(
            query=query.query,
            filters=query.filters,
            result_count=result.total,
            latency_ms=round(latency_ms, 2),
            timestamp=time.time(),
            tenant_id=query.tenant_id,
            strategy=result.strategy,
            page_size=query.page_size,
        )
        self._record(entry)

        return result

    async def count(self, query: SearchQuery) -> int:
        """Delegate count (not logged)."""
        return await self._repository.count(query)

    async def facets(self, query: SearchQuery, fields: list[str]) -> dict[str, dict[str, int]]:
        """Delegate facets (not logged)."""
        return await self._repository.facets(query, fields)

    async def suggest(self, query: SearchQuery, field: str, prefix: str, limit: int = 10) -> list[str]:
        """Delegate suggest (not logged)."""
        return await self._repository.suggest(query, field, prefix, limit)

    # ── Aggregation Queries ──────────────────────────────────────────

    def top_queries(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the top N most frequent queries.

        Returns:
            [{"query": "...", "count": 42}, ...]
        """
        counter: Counter[str] = Counter()
        with self._lock:
            for entry in self._log:
                if entry.query.strip():
                    counter[entry.query.strip()] += 1

        return [{"query": q, "count": c} for q, c in counter.most_common(n)]

    def zero_result_queries(self) -> list[dict[str, Any]]:
        """Return queries that returned zero results, with frequency.

        Returns:
            [{"query": "...", "count": 5, "last_seen": 1234567890.0}, ...]
        """
        zeros: dict[str, dict[str, Any]] = {}
        with self._lock:
            for entry in self._log:
                if entry.is_zero_result and entry.query.strip():
                    q = entry.query.strip()
                    if q not in zeros:
                        zeros[q] = {"query": q, "count": 0, "last_seen": 0.0}
                    zeros[q]["count"] += 1
                    zeros[q]["last_seen"] = max(zeros[q]["last_seen"], entry.timestamp)

        return sorted(zeros.values(), key=lambda x: x["count"], reverse=True)

    def avg_latency_by_strategy(self) -> dict[str, dict[str, Any]]:
        """Average latency grouped by search strategy.

        Returns:
            {"postgres": {"avg_ms": 12.5, "p50_ms": 10.0, "p95_ms": 25.0, "count": 100}, ...}
        """
        by_strategy: dict[str, list[float]] = defaultdict(list)
        with self._lock:
            for entry in self._log:
                by_strategy[entry.strategy].append(entry.latency_ms)

        result: dict[str, dict[str, Any]] = {}
        for strategy, latencies in by_strategy.items():
            sorted_lat = sorted(latencies)
            count = len(sorted_lat)
            result[strategy] = {
                "avg_ms": round(sum(sorted_lat) / count, 2),
                "p50_ms": round(sorted_lat[count // 2], 2),
                "p95_ms": round(sorted_lat[int(count * 0.95)] if count >= 20 else sorted_lat[-1], 2),
                "count": count,
            }

        return result

    def volume_over_time(self, hours: int = 24) -> list[dict[str, Any]]:
        """Search volume grouped by hour buckets.

        Returns:
            [{"hour": "2026-07-16T10:00:00Z", "count": 45, "avg_latency_ms": 12.3}, ...]
        """
        cutoff = time.time() - (hours * 3600)
        buckets: dict[str, dict[str, Any]] = {}

        with self._lock:
            for entry in self._log:
                if entry.timestamp < cutoff:
                    continue
                bucket = entry.hour_bucket
                if bucket not in buckets:
                    buckets[bucket] = {"hour": bucket, "count": 0, "total_latency": 0.0}
                buckets[bucket]["count"] += 1
                buckets[bucket]["total_latency"] += entry.latency_ms

        result = []
        for bucket_data in sorted(buckets.values(), key=lambda x: x["hour"]):
            count = bucket_data["count"]
            result.append({
                "hour": bucket_data["hour"],
                "count": count,
                "avg_latency_ms": round(bucket_data["total_latency"] / count, 2) if count else 0,
            })

        return result

    def summary(self) -> dict[str, Any]:
        """Return a comprehensive analytics summary."""
        with self._lock:
            total = len(self._log)
            zeros = sum(1 for e in self._log if e.is_zero_result)
            latencies = [e.latency_ms for e in self._log]
            queries = [e.query for e in self._log if e.query.strip()]

        sorted_lat = sorted(latencies) if latencies else [0]
        unique_queries = set(queries)

        return {
            "total_searches": total,
            "zero_result_count": zeros,
            "zero_result_rate": round(zeros / total, 4) if total > 0 else 0.0,
            "unique_queries": len(unique_queries),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "p50_latency_ms": round(sorted_lat[len(sorted_lat) // 2], 2),
            "p95_latency_ms": round(sorted_lat[int(len(sorted_lat) * 0.95)] if len(sorted_lat) >= 20 else sorted_lat[-1], 2),
            "top_3_queries": self.top_queries(3),
        }

    def clear(self) -> None:
        """Clear all log entries."""
        with self._lock:
            self._log.clear()
