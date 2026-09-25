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
        CONSTRAINT uq_md_review_queue_state UNIQUE (queue_type, subject_key),
        CONSTRAINT fk_md_review_queue_state_company
            FOREIGN KEY (global_company_id) REFERENCES md_global_companies (id),
        CONSTRAINT fk_md_review_queue_state_company_b
            FOREIGN KEY (global_company_id_b) REFERENCES md_global_companies (id)
    )
"""

# Applied to pre-existing tables too (CREATE TABLE IF NOT EXISTS is a no-op once
# the table exists, so the inline constraints above would never land on an
# already-materialized queue). NO ACTION is deliberate: a company that still has
# an open review row must not be deletable, which matches the Phase 6
# never-delete discipline. Idempotent via a catalog check.
FOREIGN_KEYS = [
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
             WHERE conname = 'fk_md_review_queue_state_company'
               AND conrelid = 'md_review_queue_state'::regclass
        ) THEN
            ALTER TABLE md_review_queue_state
                ADD CONSTRAINT fk_md_review_queue_state_company
                FOREIGN KEY (global_company_id) REFERENCES md_global_companies (id);
        END IF;
    END $$
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
             WHERE conname = 'fk_md_review_queue_state_company_b'
               AND conrelid = 'md_review_queue_state'::regclass
        ) THEN
            ALTER TABLE md_review_queue_state
                ADD CONSTRAINT fk_md_review_queue_state_company_b
                FOREIGN KEY (global_company_id_b) REFERENCES md_global_companies (id);
        END IF;
    END $$
    """,
]

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
        for sql in FOREIGN_KEYS:
            await conn.execute(sql)
        expected_fks = 2
        fks = await conn.fetch(
            "SELECT conname FROM pg_constraint "
            "WHERE conrelid = 'md_review_queue_state'::regclass AND contype = 'f' "
            "ORDER BY conname"
        )
        print(f"foreign keys on md_review_queue_state: {[r['conname'] for r in fks]}")
        assert len(fks) == expected_fks, f"expected {expected_fks} foreign keys, found {len(fks)}"

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
