"""Tests for the benchmark suite — runner, domains, CLI, report, API."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from benchmarks.runner import RESULTS_DIR, BenchmarkResult, BenchmarkRunner
from benchmarks.search_benchmark import (
    benchmark_fulltext_search,
    benchmark_semantic_search,
    benchmark_hybrid_search,
    benchmark_index_creation,
)
from benchmarks.nba_benchmark import (
    benchmark_nba_recommendation,
    benchmark_nba_pipeline,
    benchmark_nba_cached,
)
from benchmarks.rag_benchmark import (
    benchmark_embedding_generation,
    benchmark_vector_search,
    benchmark_full_rag_pipeline,
    benchmark_chunking_throughput,
)
from benchmarks.dashboard_benchmark import (
    benchmark_revenue_dashboard,
    benchmark_pipeline_summary,
    benchmark_concurrent_dashboard,
)
from benchmarks.api_benchmark import (
    benchmark_endpoint_latency,
    benchmark_concurrent_connections,
    benchmark_auth_overhead,
    benchmark_rate_limiter_overhead,
)


# ── BenchmarkResult tests ────────────────────────────────────────────────────

class TestBenchmarkResult:
    def test_within_budget_no_budget(self):
        r = BenchmarkResult(name="t", domain="d", p50_ms=10, p95_ms=20, p99_ms=30,
                            avg_ms=15, min_ms=5, max_ms=25, samples=10, budget_p95_ms=None)
        assert r.within_budget() is True

    def test_within_budget_under(self):
        r = BenchmarkResult(name="t", domain="d", p50_ms=10, p95_ms=20, p99_ms=30,
                            avg_ms=15, min_ms=5, max_ms=25, samples=10, budget_p95_ms=50)
        assert r.within_budget() is True

    def test_within_budget_over(self):
        r = BenchmarkResult(name="t", domain="d", p50_ms=10, p95_ms=60, p99_ms=70,
                            avg_ms=30, min_ms=5, max_ms=75, samples=10, budget_p95_ms=50)
        assert r.within_budget() is False


# ── BenchmarkRunner tests ────────────────────────────────────────────────────

class TestBenchmarkRunner:
    async def test_run_all_runs_all_registered(self):
        runner = BenchmarkRunner(version="test")

        async def bench_a():
            return BenchmarkResult(name="a", domain="test", p50_ms=1, p95_ms=2,
                                    p99_ms=3, avg_ms=1.5, min_ms=1, max_ms=3, samples=5)
        async def bench_b():
            return BenchmarkResult(name="b", domain="test", p50_ms=2, p95_ms=4,
                                    p99_ms=6, avg_ms=3, min_ms=2, max_ms=6, samples=5)

        runner.register("test", bench_a)
        runner.register("test", bench_b)
        results = await runner.run_all()
        assert len(results) == 2
        names = [r.name for r in results]
        assert "a" in names
        assert "b" in names

    async def test_run_specific_domain(self):
        runner = BenchmarkRunner(version="test")

        async def bench_a():
            return BenchmarkResult(name="a", domain="dom1", p50_ms=1, p95_ms=2,
                                    p99_ms=3, avg_ms=1.5, min_ms=1, max_ms=3, samples=5)
        async def bench_b():
            return BenchmarkResult(name="b", domain="dom2", p50_ms=2, p95_ms=4,
                                    p99_ms=6, avg_ms=3, min_ms=2, max_ms=6, samples=5)

        runner.register("dom1", bench_a)
        runner.register("dom2", bench_b)
        results = await runner.run("dom1")
        assert len(results) == 1
        assert results[0].name == "a"

    async def test_report_creates_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = BenchmarkRunner(version="test")
            runner._benchmarks["test"].append(AsyncMock(return_value=BenchmarkResult(
                name="x", domain="test", p50_ms=1, p95_ms=2, p99_ms=3,
                avg_ms=1.5, min_ms=1, max_ms=3, samples=5
            )))
            await runner.run_all()
            with patch("benchmarks.runner.RESULTS_DIR", tmp):
                run = runner.report()
                path = os.path.join(tmp, f"{run.run_id}.json")
                assert os.path.exists(path)
                with open(path) as f:
                    data = json.load(f)
                assert data["version"] == "test"
                assert len(data["results"]) == 1

    async def test_report_identifies_violations(self):
        runner = BenchmarkRunner(version="test")
        runner._benchmarks["test"].append(AsyncMock(return_value=BenchmarkResult(
            name="slow", domain="test", p50_ms=100, p95_ms=200, p99_ms=300,
            avg_ms=150, min_ms=100, max_ms=300, samples=5, budget_p95_ms=50
        )))
        await runner.run_all()
        run = runner.report()
        assert len(run.summary["violations"]) == 1
        assert run.summary["violations"][0]["name"] == "slow"

    async def test_compare_raises_on_missing_baseline(self):
        runner = BenchmarkRunner(version="test")
        with pytest.raises(FileNotFoundError):
            runner.compare("nonexistent_run")

    async def test_compare_detects_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline_data = {
                "run_id": "baseline1", "timestamp": "2024-01-01", "version": "v1",
                "results": [{"name": "bench_x", "domain": "test", "p50_ms": 10,
                             "p95_ms": 20, "p99_ms": 30, "avg_ms": 15, "min_ms": 5,
                             "max_ms": 25, "samples": 10, "unit": "ms", "metadata": {},
                             "budget_p95_ms": None}],
                "summary": {},
            }
            with open(os.path.join(tmp, "baseline1.json"), "w") as f:
                json.dump(baseline_data, f)

            runner = BenchmarkRunner(version="v2")
            runner._benchmarks["test"].append(AsyncMock(return_value=BenchmarkResult(
                name="bench_x", domain="test", p50_ms=50, p95_ms=100, p99_ms=150,
                avg_ms=70, min_ms=50, max_ms=150, samples=10,
            )))
            await runner.run_all()
            with patch("benchmarks.runner.RESULTS_DIR", tmp):
                comparison = runner.compare("baseline1")
                assert len(comparison["regressions"]) == 1
                assert comparison["regressions"][0]["name"] == "bench_x"
                assert comparison["regressions"][0]["diff_ms"] > 0

    async def test_compare_detects_improvement(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline_data = {
                "run_id": "baseline2", "timestamp": "2024-01-01", "version": "v1",
                "results": [{"name": "bench_y", "domain": "test", "p50_ms": 100,
                             "p95_ms": 200, "p99_ms": 300, "avg_ms": 150, "min_ms": 50,
                             "max_ms": 300, "samples": 10, "unit": "ms", "metadata": {},
                             "budget_p95_ms": None}],
                "summary": {},
            }
            with open(os.path.join(tmp, "baseline2.json"), "w") as f:
                json.dump(baseline_data, f)

            runner = BenchmarkRunner(version="v2")
            runner._benchmarks["test"].append(AsyncMock(return_value=BenchmarkResult(
                name="bench_y", domain="test", p50_ms=10, p95_ms=20, p99_ms=30,
                avg_ms=15, min_ms=10, max_ms=30, samples=10,
            )))
            await runner.run_all()
            with patch("benchmarks.runner.RESULTS_DIR", tmp):
                comparison = runner.compare("baseline2")
                assert len(comparison["improvements"]) == 1

    def test_list_runs_empty_when_no_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = BenchmarkRunner(version="test")
            with patch("benchmarks.runner.RESULTS_DIR", tmp):
                runs = runner.list_runs()
                assert runs == []

    def test_list_runs_returns_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i, name in enumerate(["c", "b", "a"]):
                with open(os.path.join(tmp, f"{name}.json"), "w") as f:
                    json.dump({
                        "run_id": name, "timestamp": f"2024-01-0{i+1}T00:00:00",
                        "version": "v1", "results": [],
                    }, f)
            runner = BenchmarkRunner(version="test")
            with patch("benchmarks.runner.RESULTS_DIR", tmp):
                runs = runner.list_runs()
                assert runs[0]["run_id"] == "c"


# ── Domain benchmark tests ───────────────────────────────────────────────────

class TestSearchBenchmarks:
    @pytest.mark.parametrize("bench_fn", [
        benchmark_fulltext_search,
        benchmark_semantic_search,
        benchmark_hybrid_search,
    ])
    async def test_search_benchmarks_return_three_sizes(self, bench_fn):
        results = await bench_fn()
        assert len(results) == 3
        for r in results:
            assert r.domain == "search"
            assert r.samples > 0
            assert r.p50_ms <= r.p95_ms <= r.p99_ms

    async def test_index_creation_returns_results(self):
        results = await benchmark_index_creation()
        assert len(results) == 3
        for r in results:
            assert r.domain == "search"
            assert "index_creation" in r.name


class TestNbaBenchmarks:
    @pytest.mark.parametrize("bench_fn", [
        benchmark_nba_recommendation,
        benchmark_nba_pipeline,
        benchmark_nba_cached,
    ])
    async def test_nba_benchmarks_return_three_sizes(self, bench_fn):
        results = await bench_fn()
        assert len(results) == 3
        for r in results:
            assert r.domain == "nba"
            assert r.samples > 0

    async def test_cached_is_faster_than_uncached(self):
        uncached = await benchmark_nba_recommendation()
        cached = await benchmark_nba_cached()
        for u, c in zip(uncached, cached):
            assert c.p95_ms < u.p95_ms, f"{c.name} should be faster than {u.name}"


class TestRagBenchmarks:
    @pytest.mark.parametrize("bench_fn", [
        benchmark_embedding_generation,
        benchmark_vector_search,
        benchmark_full_rag_pipeline,
        benchmark_chunking_throughput,
    ])
    async def test_rag_benchmarks_return_results(self, bench_fn):
        results = await bench_fn()
        assert len(results) >= 2
        for r in results:
            assert r.domain == "rag"
            assert r.samples > 0

    async def test_vector_search_scales_logarithmically(self):
        results = await benchmark_vector_search()
        # Larger datasets should have higher latency
        p95s = [r.p95_ms for r in results]
        assert p95s[0] <= p95s[1] <= p95s[2]


class TestDashboardBenchmarks:
    async def test_revenue_benchmark_has_cached_and_nocache(self):
        results = await benchmark_revenue_dashboard()
        assert len(results) == 2
        names = {r.name for r in results}
        assert any("cached" in n for n in names)
        assert any("nocache" in n for n in names)

    async def test_cached_faster_than_nocache(self):
        results = await benchmark_revenue_dashboard()
        cached = next(r for r in results if "cached" in r.name)
        nocache = next(r for r in results if "nocache" in r.name)
        assert cached.p95_ms < nocache.p95_ms

    async def test_concurrent_scales_with_load(self):
        results = await benchmark_concurrent_dashboard()
        p95s = [r.p95_ms for r in results]
        assert p95s == sorted(p95s), "Concurrent latency should increase with load"


class TestApiBenchmarks:
    async def test_endpoint_latency_returns_all_endpoints(self):
        results = await benchmark_endpoint_latency()
        assert len(results) >= 5

    async def test_auth_overhead_returns_three_sizes(self):
        results = await benchmark_auth_overhead()
        assert len(results) == 3

    async def test_rate_limiter_no_overhead_for_none(self):
        results = await benchmark_rate_limiter_overhead()
        none_result = next(r for r in results if r.name == "rate_limiter_overhead_none")
        assert none_result.p95_ms == 0


# ── CLI tests ────────────────────────────────────────────────────────────────

class TestCli:
    def test_cli_run_all(self):
        from benchmarks.cli import _run_benchmarks
        with patch("benchmarks.cli.os.environ", {"SALESOS_VERSION": "test"}):
            _run_benchmarks("all")

    def test_cli_run_search(self):
        from benchmarks.cli import _run_benchmarks
        with patch("benchmarks.cli.os.environ", {"SALESOS_VERSION": "test"}):
            _run_benchmarks("search")

    def test_cli_compare_missing_baseline(self):
        from benchmarks.cli import _compare
        with patch("benchmarks.cli.os.environ", {"SALESOS_VERSION": "test"}):
            with pytest.raises(SystemExit):
                _compare("nonexistent")


# ── API router tests (via internal runner helpers) ─────────────────────────

class TestBenchmarkAPI:
    def test_list_runs_via_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = BenchmarkRunner(version="test")
            with patch("benchmarks.runner.RESULTS_DIR", tmp):
                runs = runner.list_runs()
                assert runs == []

    def test_load_run_detail_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            from benchmarks.runner import RESULTS_DIR as RD
            with patch("benchmarks.runner.RESULTS_DIR", tmp):
                runner = BenchmarkRunner(version="test")
                with pytest.raises(FileNotFoundError):
                    runner.compare("nonexistent")
