"""BenchmarkRunner — orchestrates benchmark execution, result storage, comparison."""

from __future__ import annotations

import json
import os
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


@dataclass
class BenchmarkResult:
    name: str
    domain: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    samples: int
    unit: str = "ms"
    metadata: dict[str, Any] = field(default_factory=dict)
    budget_p95_ms: float | None = None

    def within_budget(self) -> bool:
        if self.budget_p95_ms is None:
            return True
        return self.p95_ms <= self.budget_p95_ms


@dataclass
class BenchmarkRun:
    run_id: str
    timestamp: str
    version: str
    results: list[dict]
    summary: dict[str, Any] = field(default_factory=dict)


class BenchmarkRunner:
    """Orchestrates benchmark suites and persists results."""

    def __init__(self, version: str = "current"):
        self.version = version
        self._results: list[BenchmarkResult] = []
        self._benchmarks: dict[str, list[Callable]] = defaultdict(list)
        os.makedirs(RESULTS_DIR, exist_ok=True)

    def register(self, domain: str, fn: Callable) -> None:
        self._benchmarks[domain].append(fn)

    async def run(self, domain: str) -> list[BenchmarkResult]:
        domain_results: list[BenchmarkResult] = []
        for fn in self._benchmarks.get(domain, []):
            res = await fn()
            if isinstance(res, list):
                domain_results.extend(res)
            else:
                domain_results.append(res)
        self._results.extend(domain_results)
        return domain_results

    async def run_all(self) -> list[BenchmarkResult]:
        for domain in list(self._benchmarks.keys()):
            await self.run(domain)
        return self._results

    def results(self) -> list[BenchmarkResult]:
        return list(self._results)

    def report(self) -> BenchmarkRun:
        run_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        serialized = [_serialize(r) for r in self._results]
        summary = {
            "total_benchmarks": len(serialized),
            "domains": sorted(set(r["domain"] for r in serialized)),
            "violations": [
                r for r in serialized
                if r.get("budget_p95_ms") is not None and r["p95_ms"] > r["budget_p95_ms"]
            ],
        }
        run = BenchmarkRun(
            run_id=run_id,
            timestamp=now,
            version=self.version,
            results=serialized,
            summary=summary,
        )
        path = os.path.join(RESULTS_DIR, f"{run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(run), f, indent=2, default=str)
        return run

    def compare(self, baseline: str) -> dict[str, Any]:
        baseline_path = os.path.join(RESULTS_DIR, f"{baseline}.json")
        if not os.path.exists(baseline_path):
            candidates = sorted(
                f.replace(".json", "") for f in os.listdir(RESULTS_DIR) if f.endswith(".json")
            )
            raise FileNotFoundError(
                f"Baseline '{baseline}' not found. Available: {candidates}"
            )
        with open(baseline_path, encoding="utf-8") as f:
            baseline_data = json.load(f)
        baseline_map = {r["name"]: r for r in baseline_data["results"]}
        comparison = {
            "baseline": baseline,
            "current_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "regressions": [],
            "improvements": [],
            "new": [],
            "missing": [],
        }
        current_map = {r.name: _serialize(r) for r in self._results}
        for name, current in current_map.items():
            if name in baseline_map:
                diff = current["p95_ms"] - baseline_map[name]["p95_ms"]
                entry = {
                    "name": name,
                    "domain": current["domain"],
                    "baseline_p95_ms": baseline_map[name]["p95_ms"],
                    "current_p95_ms": current["p95_ms"],
                    "diff_ms": round(diff, 2),
                    "diff_pct": round(
                        (diff / baseline_map[name]["p95_ms"]) * 100
                        if baseline_map[name]["p95_ms"]
                        else 0,
                        2,
                    ),
                }
                if diff > 5:
                    comparison["regressions"].append(entry)
                elif diff < -5:
                    comparison["improvements"].append(entry)
            else:
                comparison["new"].append({"name": name, "domain": current["domain"]})
        for name in baseline_map:
            if name not in current_map:
                comparison["missing"].append(name)
        return comparison

    def list_runs(self) -> list[dict]:
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


def _serialize(r: BenchmarkResult) -> dict:
    return {
        "name": r.name,
        "domain": r.domain,
        "p50_ms": r.p50_ms,
        "p95_ms": r.p95_ms,
        "p99_ms": r.p99_ms,
        "avg_ms": r.avg_ms,
        "min_ms": r.min_ms,
        "max_ms": r.max_ms,
        "samples": r.samples,
        "unit": r.unit,
        "metadata": r.metadata,
        "budget_p95_ms": r.budget_p95_ms,
    }
