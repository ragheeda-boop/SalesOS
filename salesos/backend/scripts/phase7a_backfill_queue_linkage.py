"""Backfill Global Company linkage + structured evidence on md_review_queue_state (report 114).

Root cause of the traceability gap found 2026-09-25: ReviewQueueService.record_disposition
writes only subject_key/status/disposition/reviewer/reviewed_at/notes, so a P1 row captured
with subject_key = Global Company UUID never got that UUID into the global_company_id column
and never got a structured evidence_ref. P3 rows faithfully mirrored the blanks already
present in the authoritative Phase 6 evidence CSV.

This script is record-only and adds NO new identity claim:
  * P1_CANDIDATE: copies the subject_key UUID (already validated against
    md_global_companies by phase7a_capture_gate_workbooks.py) into global_company_id.
  * P1_CANDIDATE: rebuilds evidence_ref from the G4 workbooks.
  * P3_PAIR: annotates evidence_ref with linkage_status/missing_side. It NEVER invents a
    Global Company ID - the row_a/row_b index space belongs to an external MUHIDE
    candidates file that was never ingested, so the missing IDs are unrecoverable here.

Refuses to run without --apply. Writes only md_review_queue_state in salesos_test.
Disposition, status, reviewer, reviewed_at and notes are never modified.

    python scripts/phase7a_backfill_queue_linkage.py             # dry run
    python scripts/phase7a_backfill_queue_linkage.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
import uuid
from pathlib import Path

import asyncpg

WB = Path(__file__).resolve().parents[3] / "docs" / "data" / "phase7" / "gate_review_20260925"
G4_FILES = (
    "G4_P1_CORROBORATION_SAMPLE_5PCT.csv",
    "G4_P1_FIELD_CONFLICT_FULL.csv",
    "G4_P1_WEAK_IDENTITY_FULL.csv",
)
P3_CSV = (
    Path(__file__).resolve().parents[3]
    / "docs" / "data" / "phase6" / "implementation" / "PHASE6_P3_FULL_EVIDENCE.csv"
)
EXPECTED_P1 = 643
EXPECTED_P3 = 2_661

DB = dict(host="localhost", port=5432, user="salesos",
          password="salesos_dev_password", database="salesos_test")

# Workbook columns promoted into evidence_ref. PII-free: no contact names, emails or phones.
EVIDENCE_FIELDS = (
    "review_set", "reason", "source_stratum", "ma_id", "cr_class",
    "identity_state", "sales_readiness", "non_commercial",
    "domain_relation", "exact_match_field", "error_type", "evidence_url",
)


def _val(row: dict[str, str], prefix: str) -> str:
    return next((v.strip() for k, v in row.items() if k and k.startswith(prefix)), "")


def _clean(value: str) -> str | None:
    return value or None


def read_g4() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name in G4_FILES:
        with (WB / name).open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                gid = (row.get("global_company_id") or "").strip()
                if not gid:
                    raise RuntimeError(f"{name}: row without global_company_id")
                if gid in out:
                    raise RuntimeError(f"{name}: duplicate global_company_id {gid}")
                out[gid] = {
                    "workbook": name,
                    "evidence": {
                        field: _clean(_val(row, field)) for field in EVIDENCE_FIELDS
                    } | {"workbook_decision": _clean(_val(row, "decision").upper()) or None},
                }
    return out


def read_p3() -> dict[str, str]:
    with P3_CSV.open(encoding="utf-8-sig", newline="") as fh:
        return {
            f"{r['row_a']}:{r['row_b']}": "COMPLETE" if r["company_a_global_id"] and r["company_b_global_id"]
            else ("MISSING_SIDE_B" if r["company_a_global_id"] else "MISSING_BOTH")
            for r in csv.DictReader(fh)
        }


async def main(apply: bool) -> int:
    g4, p3 = read_g4(), read_p3()
    if len(g4) != EXPECTED_P1:
        raise RuntimeError(f"expected {EXPECTED_P1} G4 workbook rows, read {len(g4)}")
    if len(p3) != EXPECTED_P3:
        raise RuntimeError(f"expected {EXPECTED_P3} P3 pairs, read {len(p3)}")

    conn = await asyncpg.connect(**DB)
    try:
        assert await conn.fetchval("SELECT current_database()") == "salesos_test", "refusing"

        db_p1 = await conn.fetch(
            "SELECT subject_key FROM md_review_queue_state WHERE queue_type='P1_CANDIDATE'"
        )
        db_keys = {str(r["subject_key"]) for r in db_p1}
        if db_keys != set(g4):
            raise RuntimeError(
                f"G4 workbook/database drift: {len(db_keys - set(g4))} in db only, "
                f"{len(set(g4) - db_keys)} in workbook only"
            )

        # Never write a Global Company ID that is not a real company.
        real = await conn.fetch(
            "SELECT id::text AS id FROM md_global_companies WHERE id::text = ANY($1::text[])",
            sorted(g4),
        )
        if len(real) != EXPECTED_P1:
            raise RuntimeError(
                f"refusing: only {len(real)}/{EXPECTED_P1} subject_keys are real companies"
            )

        stats: dict = {
            "database": "salesos_test",
            "p1_rows": EXPECTED_P1,
            "p1_rows_linked": EXPECTED_P1,
            "p1_evidence_fields": len(EVIDENCE_FIELDS) + 2,
            "p3_rows": EXPECTED_P3,
        }
        if not apply:
            stats["mode"] = "DRY RUN"
            stats["database_writes"] = 0
            print(json.dumps(stats, ensure_ascii=False, indent=1))
            return 0

        async with conn.transaction():
            p1_sql = (
                "UPDATE md_review_queue_state SET global_company_id = CAST(subject_key AS uuid), "
                "evidence_ref = CAST($2 AS JSONB) "
                "WHERE queue_type = 'P1_CANDIDATE' AND subject_key = $1"
            )
            linked = 0
            for gid, payload in g4.items():
                result = await conn.execute(p1_sql, gid, json.dumps(payload["evidence"]))
                linked += int(result.split()[-1])

            p3_sql = (
                "UPDATE md_review_queue_state SET evidence_ref = evidence_ref || CAST($2 AS JSONB) "
                "WHERE queue_type = 'P3_PAIR' AND subject_key = $1"
            )
            annotated = 0
            for subject_key, linkage in p3.items():
                extra = {"linkage_status": linkage, "linkage_source": "PHASE6_P3_FULL_EVIDENCE.csv"}
                if linkage == "MISSING_SIDE_B":
                    extra["missing_side"] = "company_b_global_id"
                elif linkage == "MISSING_BOTH":
                    extra["missing_side"] = "company_a_global_id,company_b_global_id"
                annotated += int(
                    (await conn.execute(p3_sql, subject_key, json.dumps(extra))).split()[-1]
                )
            stats["p1_rows_written"] = linked
            stats["p3_rows_written"] = annotated
        stats["mode"] = "APPLIED"
        stats["database_writes"] = linked + annotated
        print(json.dumps(stats, ensure_ascii=False, indent=1))
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.apply)))
