"""Stamp evidence_ref.linkage_status = RESOLVED on P1_CANDIDATE queue rows (report 114 §6).

Follow-up to phase7a_backfill_queue_linkage.py. That script ran on 2026-09-25 and wrote
global_company_id + a 14-field evidence_ref for the 643 G4 P1 rows, but it predates the
capture-path root fix (ReviewQueueService.record_disposition now sets linkage_status itself),
so those 643 rows are the only P1 rows in the table with no linkage_status key. Every P1 row
captured after the fix carries it.

This script is a single-key label stamp. It asserts NO new identity:
  * every target row must already have a non-null global_company_id;
  * that global_company_id must equal the subject_key (no drift);
  * that id must be a real md_global_companies row;
  * the row must be a P1_CANDIDATE whose global_company_id IS the subject (a P1 subject is
    the company), so RESOLVED is the only truthful label.
Any row failing a pre-flight assertion aborts the whole run.

Idempotent: re-running stamps 0 rows. P3/SHORT_CR/P2 rows are never touched (their
linkage_status values are more precise and were set by the earlier backfill).

Refuses to run without --apply. Writes only md_review_queue_state in salesos_test.
disposition, status, reviewer, reviewed_at, notes and global_company_id are never modified.

    python scripts/phase7a_stamp_p1_linkage_status.py             # dry run
    python scripts/phase7a_stamp_p1_linkage_status.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import asyncpg

EXPECTED_P1 = 643

DB = {
    "host": "localhost", "port": 5432, "user": "salesos",
    "password": "salesos_dev_password", "database": "salesos_test",
}

# Phase 6 tables that must be byte-identical before and after.
PHASE6_TABLES = (
    "md_source_rows", "md_global_companies", "md_global_people",
    "md_identity_classifications", "md_review_candidates", "md_contact_relationships",
    "md_industry_normalization", "md_quality_score_history", "md_sales_readiness_history",
    "md_p0_dispositions", "md_entity_merge_history", "md_entity_conflicts",
    "md_legacy_id_mappings",
)

TARGET = "P1_CANDIDATE"


async def phase6_fingerprint(conn) -> dict[str, int]:
    return {
        table: await conn.fetchval(f"SELECT count(*) FROM {table}")
        for table in PHASE6_TABLES
    }


async def main(apply: bool) -> int:
    conn = await asyncpg.connect(**DB)
    try:
        assert await conn.fetchval("SELECT current_database()") == "salesos_test", "refusing"

        before_phase6 = await phase6_fingerprint(conn)

        # Only rows that are linked, consistent, and still missing the label.
        targets = await conn.fetch(
            "SELECT subject_key, global_company_id::text AS gid FROM md_review_queue_state "
            "WHERE queue_type = $1 AND evidence_ref ? 'linkage_status' IS NOT TRUE",
            TARGET,
        )
        total_p1 = await conn.fetchval(
            "SELECT count(*) FROM md_review_queue_state WHERE queue_type = $1", TARGET
        )

        problems: list[str] = []
        if total_p1 != EXPECTED_P1:
            problems.append(f"expected {EXPECTED_P1} {TARGET} rows, found {total_p1}")

        ids: list[str] = []
        for row in targets:
            subject_key, gid = row["subject_key"], row["gid"]
            if gid is None:
                problems.append(f"{subject_key}: no global_company_id to justify a label")
                continue
            if gid != subject_key:
                problems.append(f"{subject_key}: global_company_id {gid} != subject_key")
                continue
            ids.append(gid)

        if ids:
            real = await conn.fetch(
                "SELECT id::text AS id FROM md_global_companies WHERE id::text = ANY($1::text[])",
                sorted(ids),
            )
            missing = sorted(set(ids) - {r["id"] for r in real})
            if missing:
                problems.append(f"{len(missing)} global_company_id(s) are not real companies")
        if problems:
            raise RuntimeError("refusing: " + "; ".join(problems[:5]))

        stats = {
            "database": "salesos_test",
            "queue_type": TARGET,
            "p1_rows_total": total_p1,
            "p1_rows_missing_label": len(targets),
            "label": "RESOLVED",
        }

        if not apply:
            stats["mode"] = "DRY RUN"
            stats["database_writes"] = 0
            print(json.dumps(stats, ensure_ascii=False, indent=1))
            return 0

        async with conn.transaction():
            result = await conn.execute(
                "UPDATE md_review_queue_state SET evidence_ref = jsonb_set("
                "evidence_ref, '{linkage_status}', '\"RESOLVED\"'::jsonb, true) "
                "WHERE queue_type = $1 AND evidence_ref ? 'linkage_status' IS NOT TRUE",
                TARGET,
            )
            written = int(result.split()[-1])
        stats["mode"] = "APPLIED"
        stats["database_writes"] = written

        after_phase6 = await phase6_fingerprint(conn)
        stats["phase6_unchanged"] = before_phase6 == after_phase6
        if not stats["phase6_unchanged"]:
            raise RuntimeError(f"Phase 6 tables changed: {after_phase6}")
        print(json.dumps(stats, ensure_ascii=False, indent=1))
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.apply)))
