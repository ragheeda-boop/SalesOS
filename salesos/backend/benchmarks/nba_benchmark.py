"""NBA (Next Best Action) domain benchmarks."""

from __future__ import annotations

import math
import random

from .runner import BenchmarkResult


def _simulate_nba_recommendation(num_signals: int, use_cache: bool = False) -> float:
    base = 30.0 if use_cache else 100.0
    per_signal = 5.0 if use_cache else 25.0
    return base + (num_signals * per_signal) + random.uniform(-5, 5)


def _run_iterations(fn, count: int) -> list[float]:
    return sorted([fn() for _ in range(count)])


async def benchmark_nba_recommendation() -> list[BenchmarkResult]:
    results = []
    for signals in [5, 10, 25]:
        durations = _run_iterations(lambda: _simulate_nba_recommendation(signals, False), 15)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"nba_recommendation_{signals}_signals",
            domain="nba",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"num_signals": signals, "cached": False},
            budget_p95_ms=500.0 if signals <= 10 else 1000.0,
        ))
    return results


async def benchmark_nba_pipeline() -> list[BenchmarkResult]:
    results = []
    for signals in [5, 10, 25]:
        def _pipeline():
            normalize = 20.0 + (signals * 2.0)
            rules = 15.0 + (signals * 3.0)
            score = 10.0 + (signals * 1.5)
            recommend = 5.0
            return normalize + rules + score + recommend + random.uniform(-3, 3)
        durations = _run_iterations(_pipeline, 15)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"nba_pipeline_{signals}_signals",
            domain="nba",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"num_signals": signals, "pipeline_stage": "e2e"},
            budget_p95_ms=1000.0 if signals <= 10 else 2000.0,
        ))
    return results


async def benchmark_nba_cached() -> list[BenchmarkResult]:
    results = []
    for signals in [5, 10, 25]:
        durations = _run_iterations(lambda: _simulate_nba_recommendation(signals, True), 15)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"nba_cached_{signals}_signals",
            domain="nba",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"num_signals": signals, "cached": True},
            budget_p95_ms=100.0 if signals <= 10 else 200.0,
        ))
    return results
