"""Benchmark API — list, trigger, compare benchmark runs."""

from __future__ import annotations

import json
import os
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.dependencies import require_role_dep
from benchmarks.runner import RESULTS_DIR, BenchmarkRunner

router = APIRouter(prefix="/api/v1/admin/benchmarks", tags=["Benchmarks"])


class BenchmarkRunResponse(BaseModel):
    run_id: str
    timestamp: str
    version: str
    total: int


class BenchmarkDetailResponse(BaseModel):
    run_id: str
    timestamp: str
    version: str
    results: list[dict]
    summary: dict


class BenchmarkComparisonResponse(BaseModel):
    baseline: str
    current_version: str
    timestamp: str
    regressions: list[dict]
    improvements: list[dict]
    new: list[dict]
    missing: list[str]


@router.get("", response_model=list[BenchmarkRunResponse])
async def list_benchmark_runs(
    _=Depends(require_role_dep("admin")),
):
    """List all benchmark runs."""
    runs = _load_runs()
    return runs


@router.post("/run", response_model=BenchmarkDetailResponse)
async def trigger_benchmark_run(
    request: Request,
    domain: str = Query("all", description="Domain to benchmark (or 'all')"),
    _=Depends(require_role_dep("admin")),
):
    """Trigger a new benchmark run."""
    import asyncio
    from benchmarks import search_benchmark, nba_benchmark, rag_benchmark, dashboard_benchmark, api_benchmark

    runner = BenchmarkRunner(version=_get_version(request))

    runner.register("search", search_benchmark.benchmark_fulltext_search)
    runner.register("search", search_benchmark.benchmark_semantic_search)
    runner.register("search", search_benchmark.benchmark_hybrid_search)
    runner.register("search", search_benchmark.benchmark_index_creation)
    runner.register("nba", nba_benchmark.benchmark_nba_recommendation)
    runner.register("nba", nba_benchmark.benchmark_nba_pipeline)
    runner.register("nba", nba_benchmark.benchmark_nba_cached)
    runner.register("rag", rag_benchmark.benchmark_embedding_generation)
    runner.register("rag", rag_benchmark.benchmark_vector_search)
    runner.register("rag", rag_benchmark.benchmark_full_rag_pipeline)
    runner.register("rag", rag_benchmark.benchmark_chunking_throughput)
    runner.register("dashboard", dashboard_benchmark.benchmark_revenue_dashboard)
    runner.register("dashboard", dashboard_benchmark.benchmark_pipeline_summary)
    runner.register("dashboard", dashboard_benchmark.benchmark_concurrent_dashboard)
    runner.register("api", api_benchmark.benchmark_endpoint_latency)
    runner.register("api", api_benchmark.benchmark_concurrent_connections)
    runner.register("api", api_benchmark.benchmark_auth_overhead)
    runner.register("api", api_benchmark.benchmark_rate_limiter_overhead)

    if domain == "all":
        await runner.run_all()
    else:
        await runner.run(domain)
    run = runner.report()
    return BenchmarkDetailResponse(
        run_id=run.run_id,
        timestamp=run.timestamp,
        version=run.version,
        results=run.results,
        summary=run.summary,
    )


@router.get("/latest", response_model=BenchmarkDetailResponse)
async def get_latest_benchmark(
    _=Depends(require_role_dep("admin")),
):
    """Get the latest benchmark run results."""
    runs = _load_runs()
    if not runs:
        raise HTTPException(status_code=404, detail="No benchmark runs found")
    latest = runs[0]
    return _load_run_detail(latest["run_id"])


@router.get("/compare", response_model=BenchmarkComparisonResponse)
async def compare_benchmark(
    request: Request,
    baseline: str = Query(..., description="Baseline run ID"),
    _=Depends(require_role_dep("admin")),
):
    """Compare current results against a baseline run."""
    import asyncio
    from benchmarks import search_benchmark, nba_benchmark, rag_benchmark, dashboard_benchmark, api_benchmark

    runner = BenchmarkRunner(version=_get_version(request))
    runner.register("search", search_benchmark.benchmark_fulltext_search)
    runner.register("search", search_benchmark.benchmark_semantic_search)
    runner.register("search", search_benchmark.benchmark_hybrid_search)
    runner.register("search", search_benchmark.benchmark_index_creation)
    runner.register("nba", nba_benchmark.benchmark_nba_recommendation)
    runner.register("nba", nba_benchmark.benchmark_nba_pipeline)
    runner.register("nba", nba_benchmark.benchmark_nba_cached)
    runner.register("rag", rag_benchmark.benchmark_embedding_generation)
    runner.register("rag", rag_benchmark.benchmark_vector_search)
    runner.register("rag", rag_benchmark.benchmark_full_rag_pipeline)
    runner.register("rag", rag_benchmark.benchmark_chunking_throughput)
    runner.register("dashboard", dashboard_benchmark.benchmark_revenue_dashboard)
    runner.register("dashboard", dashboard_benchmark.benchmark_pipeline_summary)
    runner.register("dashboard", dashboard_benchmark.benchmark_concurrent_dashboard)
    runner.register("api", api_benchmark.benchmark_endpoint_latency)
    runner.register("api", api_benchmark.benchmark_concurrent_connections)
    runner.register("api", api_benchmark.benchmark_auth_overhead)
    runner.register("api", api_benchmark.benchmark_rate_limiter_overhead)

    await runner.run_all()
    try:
        comparison = runner.compare(baseline)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return BenchmarkComparisonResponse(**comparison)


def _load_runs() -> list[dict]:
    runs = []
    for fname in sorted(os.listdir(RESULTS_DIR), reverse=True):
        if fname.endswith(".json"):
            path = os.path.join(RESULTS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            runs.append({
                "run_id": data.get("run_id", fname.replace(".json", "")),
                "timestamp": data.get("timestamp", ""),
                "version": data.get("version", ""),
                "total": len(data.get("results", [])),
            })
    return runs


def _load_run_detail(run_id: str) -> BenchmarkDetailResponse:
    path = os.path.join(RESULTS_DIR, f"{run_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return BenchmarkDetailResponse(
        run_id=data["run_id"],
        timestamp=data["timestamp"],
        version=data["version"],
        results=data["results"],
        summary=data["summary"],
    )


def _get_version(request: Request) -> str:
    try:
        from app.config import settings
        return settings.service_version
    except Exception:
        return "unknown"
