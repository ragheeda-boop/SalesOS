"""Phase 7A — stamp the 38 queue rows that still carry no linkage label.

Why
---
643 P1 rows, 2,661 P3 rows and 2 P2 rows are labelled. The remaining 38
(36 SHORT_CR + 2 P2_SAMPLE) are dispositioned and linked but have no
`evidence_ref.linkage_status`, so the traceability QA gate (Q1/Q3) fails and
the linkage basis of those decisions is unrecorded.

What this writes — and only this
-------------------------------
* SHORT_CR (36): `linkage_status = "RESOLVED"` — the MA-XXXXXXX subject
  resolved to a real Global Company through the legacy crosswalk, which the
  row already asserts via a non-null `global_company_id`.
* P2_SAMPLE (2): `linkage_status = "SUBJECT_NOT_A_COMPANY"` — a P2 stratum is
  not a company, matching `_resolve_company_link`. Their evidence is
  transcribed verbatim from the basis already recorded in the row's own
  `notes` (the v5 crosswalk-consistency check). Nothing is invented, and
  `real_world_truth_verified` is recorded as false because the note says so.

Idempotent: re-running writes 0 rows. Read-only with --dry-run (default).
Never touches md_global_companies, Phase 6, or any disposition.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os

import asyncpg

DSN = os.environ.get(
    "SALESOS_TEST_DSN",
    "postgresql://salesos:salesos_dev_password@localhost:5432/salesos_test",
)

# Transcribed from the P2 rows' own `notes` (PHASE7A_P2_MASTER_COMPARISON_V5.json,
# reports 91 A3 / 93 / 139). Not new judgement.
P2_EVIDENCE = {
    "sample_rows": 651,
    "strata": {"SALES_READY_WITH_REVIEW": 472, "ENRICHMENT_REQUIRED": 179},
    "classification_version": "OPTION_C_1+NCNP+DS5+LV+CR+ED",
    "stratified_rate_ref": "report 91 A3 (3%/1%)",
    "mapped_unique_master_account_id": 651,
    "duplicate_master_account_ids": 0,
    "crosswalk_failures": 0,
    "master_snapshot_rows_scanned": 296_746,
    "material_error_pct": 0.0,
    "artifact": "PHASE7A_P2_MASTER_COMPARISON_V5.json",
    "report_refs": [91, 93, 139],
    "real_world_truth_verified": False,
    "evidence_source": "transcribed from the row's own notes field",
}


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write (default: dry-run)")
    args = ap.parse_args()

    c = await asyncpg.connect(DSN)
    print(f"database: {await c.fetchval('SELECT current_database()')}")
    print(f"mode    : {'APPLY' if args.apply else 'DRY-RUN'}\n")

    # Guard: never relabel a row that already carries a label.
    pre = await c.fetchrow(
        """
        SELECT count(*) FILTER (WHERE queue_type = 'SHORT_CR') AS scr,
               count(*) FILTER (WHERE queue_type = 'SHORT_CR'
                                 AND evidence_ref ? 'linkage_status') AS scr_labelled,
               count(*) FILTER (WHERE queue_type = 'P2_SAMPLE') AS p2,
               count(*) FILTER (WHERE queue_type = 'P2_SAMPLE'
                                 AND evidence_ref ? 'linkage_status') AS p2_labelled
          FROM md_review_queue_state
        """
    )
    print("current state:")
    for k in ("scr", "scr_labelled", "p2", "p2_labelled"):
        print(f"  {k:<14} {pre[k]:,}")

    targets = await c.fetch(
        """
        SELECT id, queue_type, subject_key, global_company_id
          FROM md_review_queue_state
         WHERE queue_type IN ('SHORT_CR', 'P2_SAMPLE')
           AND NOT (evidence_ref ? 'linkage_status')
         ORDER BY queue_type, subject_key
        """
    )
    print(f"\ntargets: {len(targets)}")
    for t in targets[:5]:
        print(f"  {t['queue_type']:<12} {t['subject_key']}")
    if len(targets) > 5:
        print(f"  ... and {len(targets) - 5} more")

    if not targets:
        print("\nnothing to do (idempotent)")
        await c.close()
        return 0

    if not args.apply:
        print("\ndry-run: 0 rows written. Re-run with --apply to write.")
        await c.close()
        return 0

    written = 0
    async with c.transaction():
        for t in targets:
            if t["queue_type"] == "SHORT_CR":
                if t["global_company_id"] is None:
                    print(f"  SKIP {t['subject_key']}: no resolved company to attest")
                    continue
                patch = {
                    "linkage_status": "RESOLVED",
                    "linkage_source": "LEGACY_MUHIDE_MA_ID crosswalk",
                }
            else:
                patch = {
                    "linkage_status": "SUBJECT_NOT_A_COMPANY",
                    "linkage_source": "P2 stratum is not a company",
                    **P2_EVIDENCE,
                }
            await c.execute(
                """
                UPDATE md_review_queue_state
                   SET evidence_ref = evidence_ref || $2::jsonb
                 WHERE id = $1
                   AND NOT (evidence_ref ? 'linkage_status')
                """,
                t["id"],
                json.dumps(patch),
            )
            written += 1

    print(f"\nrows written: {written}")
    post = await c.fetchrow(
        """
        SELECT count(*) FILTER (WHERE queue_type = 'SHORT_CR'
                                 AND evidence_ref ? 'linkage_status') AS scr,
               count(*) FILTER (WHERE queue_type = 'P2_SAMPLE'
                                 AND evidence_ref ? 'linkage_status') AS p2,
               count(*) AS total
          FROM md_review_queue_state
        """
    )
    print(f"after: SHORT_CR labelled {post['scr']}, P2 labelled {post['p2']}, "
          f"total rows {post['total']}")
    await c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
