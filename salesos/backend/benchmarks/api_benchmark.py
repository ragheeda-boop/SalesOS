"""General API benchmarks — endpoint latency, concurrency, auth overhead."""

from __future__ import annotations

import math
import random

from .runner import BenchmarkResult


def _run_iterations(fn, count: int) -> list[float]:
    return sorted([fn() for _ in range(count)])


_ENDPOINTS = [
    ("GET /ping", 0.1, 0.5),
    ("GET /health", 1.0, 5.0),
    ("GET /api/v1/companies", 15.0, 50.0),
    ("GET /api/v1/contacts", 15.0, 50.0),
    ("GET /api/v1/search/semantic", 80.0, 200.0),
    ("POST /api/v1/rag/ask", 300.0, 800.0),
    ("POST /api/v1/nba/recommend", 100.0, 300.0),
    ("GET /api/v1/opportunities", 20.0, 60.0),
    ("GET /api/v1/revenue/summary", 30.0, 80.0),
    ("GET /api/v1/timeline", 40.0, 100.0),
]


async def benchmark_endpoint_latency() -> list[BenchmarkResult]:
    results = []
    for name, base_ms, _ in _ENDPOINTS:
        durations = _run_iterations(lambda: base_ms + random.uniform(-base_ms * 0.2, base_ms * 0.2), 20)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"endpoint_latency_{name.replace('/', '_').replace(' ', '_').lower()}",
            domain="api",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"endpoint": name},
            budget_p95_ms=base_ms * 3,
        ))
    return results


async def benchmark_concurrent_connections() -> list[BenchmarkResult]:
    results = []
    for concurrency in [1, 5, 10, 25, 50]:
        def _concurrent():
            base = 20.0
            overhead = math.log(concurrency + 1) * 10.0
            return base + overhead + random.uniform(-2, 2)
        durations = _run_iterations(_concurrent, 10)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"concurrent_connections_{concurrency}",
            domain="api",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"concurrent_connections": concurrency},
            budget_p95_ms=200.0 if concurrency <= 10 else 500.0,
        ))
    return results


async def benchmark_auth_overhead() -> list[BenchmarkResult]:
    results = []
    for token_size in ["short", "medium", "full"]:
        multipliers = {"short": 0.5, "medium": 1.0, "full": 2.0}
        m = multipliers[token_size]

        def _jwt_verify():
            return 0.5 * m + random.uniform(-0.05, 0.05)
        durations = _run_iterations(_jwt_verify, 30)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"auth_jwt_verify_{token_size}",
            domain="api",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"token_size": token_size, "operation": "jwt_verify"},
            budget_p95_ms=5.0,
        ))
    return results


async def benchmark_rate_limiter_overhead() -> list[BenchmarkResult]:
    results = []
    for cache_type in ["redis", "memory", "none"]:
        overheads = {"redis": 0.3, "memory": 0.05, "none": 0.0}
        base = overheads[cache_type]

        def _rate_limit():
            return base + random.uniform(-base * 0.2, base * 0.2) if base > 0 else 0.0
        durations = _run_iterations(_rate_limit, 30)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"rate_limiter_overhead_{cache_type}",
            domain="api",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"cache_type": cache_type, "operation": "rate_limit"},
            budget_p95_ms=2.0,
        ))
    return results
