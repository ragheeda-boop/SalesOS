#!/usr/bin/env python3
"""Phase 7-A — Idempotent seed of the 2,661 P3 fuzzy pairs into md_review_queue_state.

Read-only on Phase 6 data. Writes ONLY md_review_queue_state (queue_type='P3_PAIR')
in salesos_test. Idempotent: re-running never duplicates (ON CONFLICT DO NOTHING).
No merge, no CR promotion, no classification change, no production.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
import uuid

import asyncpg

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"

# Path to the Phase 6 P3 full evidence CSV (authoritative 2,661 pairs).
DEFAULT_P3_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "docs", "data", "phase6",
    "implementation", "PHASE6_P3_FULL_EVIDENCE.csv",
)

QUEUE_P3 = "P3_PAIR"


async def main() -> int:
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB
    )
    try:
        db = await conn.fetchval("SELECT current_database()")
        assert db == "salesos_test", f"REFUSING: connected to {db}, not salesos_test"
        print(f"Connected to {db} (safe).")

        csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_P3_CSV
        if not os.path.isfile(csv_path):
            print(f"P3 CSV not found at {csv_path}; aborting.")
            return 2
        print(f"Reading P3 CSV: {csv_path}")

        # Load the pairs and validate company IDs resolve to real companies.
        with open(csv_path, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        print(f"CSV rows: {len(rows)}")

        ids = {
            r["company_a_global_id"] for r in rows if r.get("company_a_global_id")
        } | {
            r["company_b_global_id"] for r in rows if r.get("company_b_global_id")
        }
        valid_company = {}
        for gid in list(ids):
            c = await conn.fetchval("SELECT COUNT(*) FROM md_global_companies WHERE id = $1", gid)
            valid_company[gid] = bool(c)
        invalid = {gid for gid, ok in valid_company.items() if not ok}
        print(f"Distinct company ids: {len(ids)}; invalid (not real company): {len(invalid)}")
        if invalid:
            # Refuse to seed any pair referencing a non-real company (Global ID integrity).
            print(f"ABORT: {len(invalid)} non-real company ids found (first 5): {list(invalid)[:5]}")
            return 3

        # Before snapshots for the report.
        before_p3 = await conn.fetchval(
            "SELECT COUNT(*) FROM md_review_queue_state WHERE queue_type = $1", QUEUE_P3
        )

        seed_rows = []
        for r in rows:
            pair_id = r["pair_id"] or f"FZ-{r['row_a']}-{r['row_b']}"
            subject_key = f"{r['row_a']}:{r['row_b']}"
            seed_rows.append((
                str(uuid.uuid5(uuid.NAMESPACE_DNS, f"p7a:{QUEUE_P3}:{subject_key}")),
                QUEUE_P3,
                subject_key,
                r["company_a_global_id"] or None,
                r["company_b_global_id"] or None,
                json.dumps({
                    "source_id": r.get("source_id") or "",
                    "reason": r.get("reason") or "FUZZY_NAME_SIMILARITY",
                    "pair_id": pair_id,
                    "final_review_required": r.get("final_review_required") or "YES",
                    "evidence_type": r.get("evidence_type") or "FUZZY",
                }),
            ))

        await conn.executemany(
            "INSERT INTO md_review_queue_state "
            "(id, queue_type, subject_key, global_company_id, global_company_id_b, evidence_ref, status) "
            "VALUES ($1::uuid, $2, $3, $4::uuid, $5::uuid, CAST($6 AS JSONB), 'pending') "
            "ON CONFLICT (queue_type, subject_key) DO NOTHING",
            seed_rows,
        )

        after_p3 = await conn.fetchval(
            "SELECT COUNT(*) FROM md_review_queue_state WHERE queue_type = $1", QUEUE_P3
        )
        # Verify no duplicates.
        dup_check = await conn.fetchval(
            "SELECT COUNT(*) FROM ("
            "SELECT queue_type, subject_key, COUNT(*) c FROM md_review_queue_state "
            "WHERE queue_type = $1 GROUP BY queue_type, subject_key HAVING COUNT(*)>1) x",
            QUEUE_P3,
        )
        print(f"\nP3 seed: before={before_p3} after={after_p3} (delta={after_p3-before_p3})")
        print(f"duplicate logical records after seed: {dup_check}")
        print(f"expected pair count: {len(rows)}")
        if after_p3 == len(rows) and dup_check == 0:
            print("\nP3 SEED: PASS (2,661 pairs, no duplicates)")
            return 0
        print("\nP3 SEED: CHECK NEEDED — verify expected count")
        return 1
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
