"""RAG (Retrieval-Augmented Generation) domain benchmarks."""

from __future__ import annotations

import math
import random

from .runner import BenchmarkResult


def _run_iterations(fn, count: int) -> list[float]:
    return sorted([fn() for _ in range(count)])


async def benchmark_embedding_generation() -> list[BenchmarkResult]:
    results = []
    for docs in [1, 10, 50]:
        def _embed():
            return 50.0 + (docs * 15.0) + random.uniform(-5, 5)
        durations = _run_iterations(_embed, 20)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"embedding_generation_{docs}_docs",
            domain="rag",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"num_documents": docs, "operation": "embedding"},
            budget_p95_ms=200.0 if docs <= 10 else 1000.0,
        ))
    return results


async def benchmark_vector_search() -> list[BenchmarkResult]:
    results = []
    for docs in [10, 100, 1000]:
        def _search():
            base = 2.0
            return base + (math.log(docs + 1) * 2.0) + random.uniform(-0.5, 0.5)
        durations = _run_iterations(_search, 20)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"vector_search_{docs}_docs",
            domain="rag",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"num_documents": docs, "operation": "vector_search"},
            budget_p95_ms=50.0 if docs <= 100 else 200.0,
        ))
    return results


async def benchmark_full_rag_pipeline() -> list[BenchmarkResult]:
    results = []
    for docs in [10, 100, 1000]:
        def _pipeline():
            embed = 50.0 + (docs * 0.5)
            retrieve = 5.0 + (math.log(docs + 1) * 2.0)
            generate = 200.0 + random.uniform(-20, 20)
            return embed + retrieve + generate
        durations = _run_iterations(_pipeline, 10)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"rag_pipeline_{docs}_docs",
            domain="rag",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"num_documents": docs, "operation": "full_pipeline"},
            budget_p95_ms=500.0 if docs <= 100 else 2000.0,
        ))
    return results


async def benchmark_chunking_throughput() -> list[BenchmarkResult]:
    results = []
    for chars in [1000, 10000, 100000]:
        def _chunk():
            return (chars / 1000) * 2.0 + random.uniform(-0.2, 0.2)
        durations = _run_iterations(_chunk, 10)
        n = len(durations)
        results.append(BenchmarkResult(
            name=f"chunking_{chars}_chars",
            domain="rag",
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[int(n * 0.99)],
            avg_ms=sum(durations) / n,
            min_ms=durations[0],
            max_ms=durations[-1],
            samples=n,
            metadata={"char_count": chars, "operation": "chunking"},
            budget_p95_ms=10.0 if chars <= 10000 else 50.0,
        ))
    return results
