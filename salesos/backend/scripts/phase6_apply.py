"""Apply the Phase 6 enrichment pipeline to salesos_test (non-dry-run).

The dry-run harness (scripts/phase6_dry_run.py) is the safe default: it performs
zero writes and every safety counter must be 0. This script is the deliberate
opt-out of that, and exists because the Phase 7 read-side tests
(test_phase7a_review_queue_db, test_phase7_sales_usability_http,
test_muhide_rehousing_db) assert on the *output* of the pipeline — review
candidate counts, sales-readiness distribution, identity classifications — which
is empty on a freshly migrated database:

    md_review_candidates        0
    md_identity_classifications 0
    md_global_companies         296746

So a green Phase 7 suite is not reachable without applying the pipeline at least
once to the test database.

Safety properties, deliberately mirroring the dry-run harness:

  * Refuses to run against anything other than salesos_test. The persistent local
    development database is never a target.
  * Bounded runs are refused outright: Phase6Pipeline.run() rejects
    max_accounts unless dry_run, so a partial apply cannot leave a half-populated
    review queue that still looks plausible.
  * Runs WITHOUT an enclosing transaction: the apply path streams bounded
    batches under asyncpg autocommit and every write is idempotent
    (deterministic uuid5 keys, ON CONFLICT DO NOTHING), so an interrupted run
    is healed by running it again. Wrapping the whole run in one explicit
    transaction would instead hold every batch's locks for the entire duration
    — the exact stall the batching exists to avoid.
  * Prints the safety counters afterwards. The pipeline's own contract is that
    the source-immutability counters stay 0 even on a real run.

Usage:  python scripts/phase6_apply.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.master_data.phase6.pipeline import Phase6Pipeline  # noqa: E402

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"


async def main() -> int:
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB
    )
    try:
        db = await conn.fetchval("SELECT current_database()")
        if db != "salesos_test":
            raise SystemExit(f"REFUSING: connected to {db}, not salesos_test")

        existing = await conn.fetchval("SELECT count(*) FROM md_review_candidates")
        if existing:
            print(f"md_review_candidates already holds {existing} rows.")
            print("Re-applying is idempotent by design, but confirm this is intended.")

        started = time.time()
        # Deliberately NOT wrapped in a single transaction. Phase6Pipeline
        # writes in bounded batches and relies on asyncpg's autocommit so each
        # batch is durable as it is sent; one outer transaction would hold every
        # batch's locks until the end. Interrupting the run is safe either way
        # because every write uses a deterministic uuid5 key with
        # ON CONFLICT DO NOTHING, so re-running resumes rather than duplicates.
        pipeline = Phase6Pipeline(conn, dry_run=False)
        result = await pipeline.run()
        summary = result.get("summary", {})
        staged = result.get("staged", {})
        elapsed = time.time() - started

        print(f"\nApply finished in {elapsed:,.0f}s")
        print(f"  master_accounts_loaded : {summary.get('master_accounts_loaded')}")
        for table, count in sorted(staged.items()):
            print(f"  staged {table:<34} {count}")
        print(f"  safety counters: {dict(pipeline.safety)}")
        for name, value in pipeline.safety.items():
            if value:
                raise SystemExit(f"ABORTING: safety counter {name} = {value}")

        # Post-conditions read back from committed state, not from the returned
        # summary: the point is what is actually in the tables now.
        print("\nCommitted row counts:")
        for table in (
            "md_identity_classifications",
            "md_review_candidates",
            "md_industry_normalization",
            "md_quality_score_history",
            "md_sales_readiness_history",
            "md_contact_relationships",
        ):
            count = await conn.fetchval(f"SELECT count(*) FROM {table}")
            print(f"  {table:<34} {count}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
