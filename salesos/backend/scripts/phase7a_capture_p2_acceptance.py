#!/usr/bin/env python3
"""Capture the authorized P2 sample acceptance in the review queue.

This is a record-only operation on ``salesos_test``.  It does not change the
46,736 P2 candidates, Master Data, readiness, identity, source rows, or any
production database.  The acceptance records the completed deterministic
sample review (zero observed material errors in both strata) so the decision
is visible in the Phase 7-A queue and auditable.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.modules.master_data.phase7.review_queue import (
    QUEUE_P2_SAMPLE,
    ReviewQueueService,
    review_async_session,
)
from app.modules.master_data.phase7.schemas import P2SampleDisposition

REVIEWER = "authorized-human-reviewer:p2-sample-2026-09-22"
SAMPLE_SHA = "f1903a82db416fd746d797907bcb6dba4d73b21edb4204b34187e263592daffa"
MASTER_SHA = "4dc9ead7224512ac5db30f8a412b67c1df7ba319c6fa6bed3017bdd994cd36b1"

STRATA = {
    "P2:SALES_READY_WITH_REVIEW": "1,119/1,119 reviewed; 0.00% material error; threshold 2.00%.",
    "P2:ENRICHMENT_REQUIRED": "94/94 reviewed; 0.00% material error; threshold 2.00%.",
}


async def main() -> int:
    async with review_async_session() as session:
        svc = ReviewQueueService(session=session)
        await svc._assert_write_db()
        # Capture a stable safety baseline before any write.
        before = dict(
            (r["table_name"], int(r["count"]))
            for r in (await session.execute(text("""
                SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
                UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
                UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
                UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
                UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
                UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
            """))).mappings().all()
        )
        notes_common = (
            "Authorized human review of deterministic P2 sample against official Master Accounts. "
            "Sample SHA-256=" + SAMPLE_SHA + "; Master SHA-256=" + MASTER_SHA + ". "
            "Capture-only: accepts the stratum sample result; does not approve the full population, "
            "promote fields, merge entities, or authorize production."
        )
        for subject, result in STRATA.items():
            await svc.record_disposition(
                queue_type=QUEUE_P2_SAMPLE,
                subject_key=subject,
                disposition=P2SampleDisposition.ACCEPT_SAMPLE.value,
                reviewer=REVIEWER,
                notes=notes_common + " " + result,
            )
        after = dict(
            (r["table_name"], int(r["count"]))
            for r in (await session.execute(text("""
                SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
                UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
                UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
                UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
                UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
                UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
            """))).mappings().all()
        )
        if before != after:
            raise RuntimeError(f"Safety failure: Phase 6 counts changed: before={before}, after={after}")
        rows = (await session.execute(text("""
            SELECT queue_type, subject_key, status, disposition, reviewer
            FROM md_review_queue_state
            WHERE queue_type = :q AND subject_key LIKE 'P2:%'
            ORDER BY subject_key
        """), {"q": QUEUE_P2_SAMPLE})).mappings().all()
        print({"database": "salesos_test", "phase6_counts_unchanged": True,
               "captured": [dict(r) for r in rows]})
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
