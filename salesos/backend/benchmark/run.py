#!/usr/bin/env python
"""SalesOS Benchmark — Phase 1 of Sprint 3.

Generates synthetic data at various scales, runs benchmark queries,
and produces a comprehensive Markdown report with EXPLAIN ANALYZE.

Usage:
    # Smoke test with SQLite (no PostgreSQL needed):
    python -m benchmark.run --dataset 100 --iterations 2 --engine sqlite

    # Full benchmark with PostgreSQL:
    DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/salesos_test \
    python -m benchmark.run --dataset all --iterations 5

    # Custom:
    python -m benchmark.run --dataset 1000 --iterations 3 --output reports/benchmark.md
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

# Ensure backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from benchmark.data_generator import DataGenerator
from benchmark.queries import get_queries_for_dataset
from benchmark.reporter import generate_json_report, generate_report
from benchmark.runner import run_benchmark

DATASET_SIZES = [100, 1_000, 10_000, 100_000]
DEFAULT_DSN = "sqlite+aiosqlite:///./benchmark.db"


async def ensure_tables(db: AsyncSession, engine_is_pg: bool = False) -> None:
    """Drop and recreate companies table."""
    await db.execute(text("DROP TABLE IF EXISTS companies CASCADE"))
    col_type = "UUID" if engine_is_pg else "TEXT"
    ts_type = "TIMESTAMPTZ" if engine_is_pg else "TEXT"
    await db.execute(text(f"""
        CREATE TABLE companies (
            id {col_type} PRIMARY KEY,
            tenant_id {col_type} NOT NULL,
            name_ar VARCHAR(500) NOT NULL,
            name_en VARCHAR(500),
            cr_number VARCHAR(50) NOT NULL,
            cr_type VARCHAR(50),
            status VARCHAR(50) DEFAULT 'active',
            city VARCHAR(200),
            region VARCHAR(200),
            phone VARCHAR(50),
            email VARCHAR(255),
            address TEXT,
            activity_description TEXT,
            activity_code VARCHAR(50),
            legal_form VARCHAR(100),
            capital FLOAT,
            employees_count INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            confidence_score FLOAT DEFAULT 0.0,
            latitude FLOAT,
            longitude FLOAT,
            created_at {ts_type},
            updated_at {ts_type}
        )
    """))
    await db.commit()


async def ensure_indexes(db: AsyncSession, engine_is_pg: bool) -> None:
    """Create optimized indexes for benchmark."""
    if not engine_is_pg:
        return

    indexes = [
        # Composite B-tree for tenant-scoped exact search and sorting
        "CREATE INDEX IF NOT EXISTS idx_companies_tenant_name_ar ON companies(tenant_id, name_ar)",
        "CREATE INDEX IF NOT EXISTS idx_companies_tenant_cr ON companies(tenant_id, cr_number)",
        "CREATE INDEX IF NOT EXISTS idx_companies_tenant_city ON companies(tenant_id, city)",
        "CREATE INDEX IF NOT EXISTS idx_companies_tenant_created ON companies(tenant_id, created_at)",
        # GIN trigram for ILIKE / partial search
        "CREATE INDEX IF NOT EXISTS idx_companies_name_ar_trgm ON companies USING GIN (name_ar gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS idx_companies_cr_number_trgm ON companies USING GIN (cr_number gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS idx_companies_city_trgm ON companies USING GIN (city gin_trgm_ops)",
    ]
    for idx in indexes:
        try:
            await db.execute(text(idx))
        except Exception as e:
            print(f"  [WARN] Index: {e}")
    await db.commit()


async def get_company_count(db: AsyncSession) -> int:
    result = await db.execute(text("SELECT COUNT(*) FROM companies"))
    return result.scalar() or 0


async def main():
    parser = argparse.ArgumentParser(description="SalesOS Benchmark")
    parser.add_argument("--dataset", type=str, default="100",
                        help="Dataset size: 100, 1000, 10000, 100000, or 'all'")
    parser.add_argument("--iterations", type=int, default=5,
                        help="Number of iterations per query")
    parser.add_argument("--output", type=str, default="",
                        help="Output file path for the report")
    parser.add_argument("--engine", type=str, default="auto",
                        choices=["auto", "postgresql", "sqlite"],
                        help="Database engine override")
    args = parser.parse_args()

    # Determine dataset sizes
    if args.dataset == "all":
        sizes = DATASET_SIZES
    else:
        sizes = [int(args.dataset)]

    # Determine DSN
    dsn = os.environ.get("DATABASE_URL", DEFAULT_DSN)
    engine_is_pg = "postgresql" in dsn or "asyncpg" in dsn

    if args.engine == "sqlite":
        dsn = DEFAULT_DSN
        engine_is_pg = False
    elif args.engine == "postgresql" and not engine_is_pg:
        print("ERROR: --engine postgresql requires DATABASE_URL with postgresql+asyncpg://")
        sys.exit(1)

    print("[BENCHMARK] SalesOS Benchmark")
    print(f"  Engine: {'PostgreSQL' if engine_is_pg else 'SQLite'}")
    print(f"  DSN: {dsn}")
    print(f"  Dataset(s): {', '.join(f'{s:,}' for s in sizes)}")
    print(f"  Iterations per query: {args.iterations}")
    print()

    # Connect
    engine = create_async_engine(dsn, echo=False)
    async with engine.connect() as conn:
        db = AsyncSession(bind=conn)

        # Ensure schema
        print("[SETUP] Ensuring tables...")
        await ensure_tables(db, engine_is_pg)

        if engine_is_pg:
            print("[SETUP] Ensuring indexes...")
            await ensure_indexes(db, engine_is_pg)

        # Get or create a test tenant
        test_tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

        # Run benchmarks for each dataset size
        all_results = []
        for dataset_size in sizes:
            current_count = await get_company_count(db)
            print(f"\n[DATASET] {dataset_size:,} companies")
            print(f"  Current DB has: {current_count:,}")

            if current_count < dataset_size:
                needed = dataset_size - current_count
                print(f"  Generating {needed:,} additional companies...")

                gen = DataGenerator(seed=dataset_size)
                companies = gen.generate_companies(test_tenant_id, needed)

                await DataGenerator.async_seed_database(db, companies)
                print(f"  Inserted {len(companies):,} companies")

            queries = get_queries_for_dataset(dataset_size)

            # Update tenant_id in params
            for q in queries:
                for k, v in q["params"].items():
                    if "tenant_id" in k:
                        q["params"][k] = str(test_tenant_id)

            print(f"  Running {len(queries)} queries x {args.iterations} iterations...")
            results = await run_benchmark(db, queries, iterations=args.iterations, dataset_size=dataset_size, engine_is_pg=engine_is_pg)
            all_results.extend(results)

            # Print quick summary
            p95_vals = [r.p95_ms for r in results]
            print(f"  [OK] p95 range: {min(p95_vals):.2f}ms to {max(p95_vals):.2f}ms")

    await engine.dispose()

    # Generate report
    report_md = generate_report(all_results)
    report_json = generate_json_report(all_results)

    output_path = args.output or ""
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/benchmark_{ts}.md"

    # Ensure output directory
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    Path(output_path).write_text(report_md, encoding="utf-8")
    print(f"\n[REPORT] Markdown: {output_path}")

    json_path = output_path.replace(".md", ".json")
    if json_path == output_path:
        json_path = output_path + ".json"
    import json
    Path(json_path).write_text(json.dumps(report_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[REPORT] JSON: {json_path}")

    print("\n[COMPLETE] Benchmark finished.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
