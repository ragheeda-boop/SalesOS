"""SalesOS Benchmark Framework — Sprint 3 Phase 1.

Usage:
    python -m benchmark.run --dataset 1000 --iterations 5
    python -m benchmark.run --dataset all --iterations 3 --output reports/benchmark.md

Requires:
    - A running PostgreSQL (or SQLite for smoke-test)
    - DATABASE_URL env var (defaults to sqlite for testing)
"""
