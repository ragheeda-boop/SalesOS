#!/usr/bin/env python3
"""Phase 7-A — SCHEMA GATE for salesos_test (idempotent, rollback-safe).

Materializes ONLY the review-tooling state table `md_review_queue_state` on
**salesos_test only**. This is the single permitted Phase 7-A write target.

Safety guarantees:
  - CREATE TABLE IF NOT EXISTS (idempotent; safe to run twice).
  - NEVER modifies any existing table/row.
  - No RLS (GLOBAL table, matching the Phase 6 global-table convention).
  - Does NOT touch the `salesos` production database.
  - Deterministic unique constraint (queue_type, subject_key) for idempotent seeding.
"""

from __future__ import annotations

import asyncio
import sys

import asyncpg

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"

REVIEW_STATE_DDL = """
    CREATE TABLE IF NOT EXISTS md_review_queue_state (
        id UUID PRIMARY KEY,
        queue_type VARCHAR(32) NOT NULL,           -- P3_PAIR / SHORT_CR / TRIAGE
        subject_key VARCHAR(128) NOT NULL,         -- P3: row_a:row_b ; SHORT_CR/TRIAGE: global_company_id
        global_company_id UUID,                    -- primary company under review
        global_company_id_b UUID,                  -- P3 pair's second company
        evidence_ref JSONB NOT NULL DEFAULT '{}',  -- curated evidence (no source payload copy)
        status VARCHAR(24) NOT NULL DEFAULT 'pending',   -- pending/in_review/dispositioned/escalated
        disposition VARCHAR(32),                   -- record-only capture; no side effects
        reviewer VARCHAR(255),
        reviewed_at TIMESTAMPTZ,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_md_review_queue_state UNIQUE (queue_type, subject_key)
    )
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_md_review_queue_state_qtype ON md_review_queue_state (queue_type, status)",
    "CREATE INDEX IF NOT EXISTS ix_md_review_queue_state_company ON md_review_queue_state (global_company_id)",
    "CREATE INDEX IF NOT EXISTS ix_md_review_queue_state_company_b ON md_review_queue_state (global_company_id_b)",
]


async def main() -> int:
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB
    )
    try:
        db = await conn.fetchval("SELECT current_database()")
        assert db == "salesos_test", f"REFUSING: connected to {db}, not salesos_test"
        print(f"Connected to {db} (safe).")

        # Snapshot before (existing tables unchanged).
        before = set(
            r["tablename"]
            for r in await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'md_%'"
            )
        )
        exists_before = "md_review_queue_state" in before

        await conn.execute(REVIEW_STATE_DDL)
        for sql in INDEXES:
            await conn.execute(sql)

        after = set(
            r["tablename"]
            for r in await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'md_%'"
            )
        )
        created = "md_review_queue_state" if "md_review_queue_state" not in before else "already existed (idempotent)"
        print(f"md_review_queue_state: {created}")
        print(f"md_ tables before={len(before)} after={len(after)} (delta={len(after)-len(before)})")

        # Verify no OTHER table changed.
        added_only = after - before
        assert added_only <= {"md_review_queue_state"}, f"Unexpected tables added: {added_only - {'md_review_queue_state'}}"
        print("Only md_review_queue_state added; no other table touched.")

        # Idempotency probe.
        await conn.execute("BEGIN")
        await conn.execute(REVIEW_STATE_DDL)
        await conn.execute("ROLLBACK")
        print("Idempotency: second CREATE of md_review_queue_state OK (no error)")

        print("\nSCHEMA GATE (Phase 7-A): PASS")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
