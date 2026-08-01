"""Benchmark runner — executes queries, measures timing, collects EXPLAIN ANALYZE.

CI-19 Wave 2 Slice 6: no sqlalchemy.text — allowlisted SQL via exec_driver_sql.
"""

from __future__ import annotations

import re
import time

from sqlalchemy.ext.asyncio import AsyncSession

# Named bind markers in allowlisted benchmark SQL (queries.py). Avoid matching ::casts.
_NAMED_PARAM_RE = re.compile(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)")


def normalize_sql(sql: str, engine_is_pg: bool = False) -> str:
    """Normalize SQL for database compatibility.

    Strips ::uuid casts (columns are TEXT for cross-DB compatibility).
    Replaces ILIKE with LIKE for SQLite.
    """
    sql = sql.replace("::uuid", "")
    if not engine_is_pg:
        sql = sql.replace("ILIKE", "LIKE")
        sql = sql.replace("NULLS LAST", "")
        sql = sql.replace("NULLS FIRST", "")
    return sql


def _driver_sql_and_params(
    sql: str, params: dict, engine_is_pg: bool
) -> tuple[str, list | dict]:
    """Convert :named binds to dialect positional markers for exec_driver_sql."""
    if not params:
        return sql, {}
    names: list[str] = []

    def _repl(match: re.Match[str]) -> str:
        names.append(match.group(1))
        return f"${len(names)}" if engine_is_pg else "?"

    out = _NAMED_PARAM_RE.sub(_repl, sql)
    values = [params[n] for n in names]
    return out, values


class BenchmarkResult:
    """Result of benchmarking a single query at a single dataset size."""

    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        dataset_size: int,
        durations_ms: list[float],
        explain_output: str | None = None,
        row_count: int = 0,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.dataset_size = dataset_size
        self.durations_ms = sorted(durations_ms)
        self.explain_output = explain_output
        self.row_count = row_count

    @property
    def min_ms(self) -> float:
        return self.durations_ms[0] if self.durations_ms else 0.0

    @property
    def max_ms(self) -> float:
        return self.durations_ms[-1] if self.durations_ms else 0.0

    @property
    def avg_ms(self) -> float:
        return sum(self.durations_ms) / len(self.durations_ms) if self.durations_ms else 0.0

    @property
    def p50_ms(self) -> float:
        return self._percentile(50)

    @property
    def p95_ms(self) -> float:
        return self._percentile(95)

    @property
    def p99_ms(self) -> float:
        return self._percentile(99)

    def _percentile(self, p: int) -> float:
        if not self.durations_ms:
            return 0.0
        idx = max(0, int(len(self.durations_ms) * p / 100) - 1)
        return self.durations_ms[idx]


async def run_benchmark(
    db: AsyncSession,
    queries: list[dict],
    iterations: int = 5,
    dataset_size: int = 0,
    engine_is_pg: bool = False,
) -> list[BenchmarkResult]:
    """Run all queries for iterations times and return BenchmarkResults."""
    results: list[BenchmarkResult] = []
    conn = await db.connection()

    for q in queries:
        durations: list[float] = []
        explain_output: str | None = None
        row_count = 0

        sql = normalize_sql(q["sql"], engine_is_pg)
        driver_sql, driver_params = _driver_sql_and_params(sql, q["params"], engine_is_pg)

        for i in range(iterations):
            start = time.monotonic()
            result = await conn.exec_driver_sql(driver_sql, driver_params)
            elapsed = (time.monotonic() - start) * 1000
            durations.append(elapsed)

            rows = list(result)
            if i == 0:
                row_count = len(rows)

        # Run EXPLAIN ANALYZE on last iteration if requested
        if q.get("explain", False):
            try:
                explain_sql, explain_params = _driver_sql_and_params(
                    f"EXPLAIN ANALYZE {sql}", q["params"], engine_is_pg
                )
                result = await conn.exec_driver_sql(explain_sql, explain_params)
                explain_lines = [str(row[0]) for row in result]
                explain_output = "\n".join(explain_lines)
            except Exception as e:
                explain_output = f"(EXPLAIN ANALYZE not supported: {e})"

        results.append(
            BenchmarkResult(
                name=q["name"],
                description=q["description"],
                category=q["category"],
                dataset_size=dataset_size,
                durations_ms=durations,
                explain_output=explain_output,
                row_count=row_count,
            )
        )

    return results
