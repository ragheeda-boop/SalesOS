"""SalesOS Benchmark Suite — performance regression detection framework.

Usage:
    python -m benchmarks run all
    python -m benchmarks run search
    python -m benchmarks compare --baseline v0.8
    python -m benchmarks report --format html
"""

from __future__ import annotations

from .runner import BenchmarkRunner, BenchmarkResult

__all__ = ["BenchmarkRunner", "BenchmarkResult"]
