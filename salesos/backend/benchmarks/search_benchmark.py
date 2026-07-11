"""Search domain benchmarks — full-text, semantic, hybrid, index time."""

from __future__ import annotations

import math
import time

from .runner import BenchmarkResult


def _simulate_search_latency(record_count: int, base_ms: float = 5.0) -> float:
    """Simulate search latency scaling with record count."""
    return base_ms + (record_count * 0.001) + (math.log(record_count + 1) * 0.5)


def _simulate_embedding_latency(dimensions: int = 1536) -> float:
    return 20.0 + (dimensions * 0.01)


def _run_iterations(fn, count: int) -> list[float]:
    return [fn() for _ in range(count)]


async def benchmark_fulltext_search() -> list[BenchmarkResult]:
    results = []
    for records in [100, 1000, 10000]:
        durations = _run_iterations(lambda: _simulate_search_latency(records, 3.0), 20)
        durations.sort()
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"fulltext_search_{records}",
            domain="search",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"record_count": records, "search_type": "fulltext"},
            budget_p95_ms=200.0 if records <= 1000 else 500.0,
        ))
    return results


async def benchmark_semantic_search() -> list[BenchmarkResult]:
    results = []
    for records in [100, 1000, 10000]:
        durations = _run_iterations(
            lambda: _simulate_search_latency(records, 10.0) + _simulate_embedding_latency(), 20
        )
        durations.sort()
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"semantic_search_{records}",
            domain="search",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"record_count": records, "search_type": "semantic"},
            budget_p95_ms=500.0 if records <= 1000 else 1000.0,
        ))
    return results


async def benchmark_hybrid_search() -> list[BenchmarkResult]:
    results = []
    for records in [100, 1000, 10000]:
        durations = _run_iterations(
            lambda: _simulate_search_latency(records, 15.0) + _simulate_embedding_latency(), 20
        )
        durations.sort()
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"hybrid_search_{records}",
            domain="search",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"record_count": records, "search_type": "hybrid"},
            budget_p95_ms=800.0 if records <= 1000 else 2000.0,
        ))
    return results


async def benchmark_index_creation() -> list[BenchmarkResult]:
    """Simulate index creation time for different record counts."""
    results = []
    for records in [100, 1000, 10000]:
        def _create_index():
            base = 50.0
            return base + (records * 0.05) + (_simulate_embedding_latency() * records * 0.1)
        durations = _run_iterations(_create_index, 5)
        durations.sort()
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"index_creation_{records}",
            domain="search",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"record_count": records, "search_type": "index_creation"},
            budget_p95_ms=5000.0 if records <= 1000 else 30000.0,
        ))
    return results
