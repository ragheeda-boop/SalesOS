#!/usr/bin/env python3
"""Capture the four PO-authorized P1/Short-CR overlap confirmations.

This is deliberately narrow and record-only. It never changes a Phase 6 row,
promotes a CR, merges entities, or touches production. Without --apply it is
a read-only preflight; --apply writes only P1_CANDIDATE rows in salesos_test.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.master_data.phase7.review_queue import (
    QUEUE_P1,
    ReviewQueueService,
    review_async_session,
)

TARGETS = (
    "48777b92-94d9-48be-9b04-a741b54bf110",
    "490bcf8d-b018-4001-b545-5a6fb8bab811",
    "a68fe4f6-728e-4739-8655-003f6d92bf60",
    "eeb94268-0181-4dc6-b2fb-ea872f9ddb19",
)
REVIEWER = "authorized-human-reviewer:p1-short-cr-overlap"
NOTES = (
    "PHASE7A_PO_DECISION_2026-09-09 D3: CONFIRM. "
    "Same account already has Short-CR CONFIRMED_ARTIFACT; "
    "record-only, no classification change."
)
PHASE6_TABLES = (
    "md_global_companies",
    "md_identity_classifications",
    "md_review_candidates",
    "md_sales_readiness_history",
    "md_source_rows",
)


async def main(apply: bool) -> int:
    async with review_async_session() as session:
        svc = ReviewQueueService(session=session)
        db = await svc._current_db()
        before = {
            table: (await session.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()
            for table in PHASE6_TABLES
        }
        rows = (
            await session.execute(
                text(
                    "SELECT global_entity_id::text AS gid, status, decision "
                    "FROM md_review_candidates "
                    "WHERE candidate_type='P1' AND global_entity_id = ANY(:gids) "
                    "ORDER BY global_entity_id"
                ),
                {"gids": list(TARGETS)},
            )
        ).mappings().all()
        state_before = (
            await session.execute(
                text(
                    "SELECT subject_key, status, disposition FROM md_review_queue_state "
                    "WHERE queue_type=:q AND subject_key = ANY(:keys) ORDER BY subject_key"
                ),
                {"q": QUEUE_P1, "keys": list(TARGETS)},
            )
        ).mappings().all()
        if len(rows) != len(TARGETS):
            raise RuntimeError(f"Expected four P1 candidates, found {len(rows)}")
        if any(r["status"] != "pending" or r["decision"] is not None for r in rows):
            raise RuntimeError("A target P1 candidate is no longer pending; refusing capture")
        if not apply:
            print(json.dumps({"database": db, "mode": "DRY_RUN", "targets": list(TARGETS), "existing_p1_state": [dict(r) for r in state_before]}))
            return 0
        for gid in TARGETS:
            await svc.record_disposition(
                queue_type=QUEUE_P1,
                subject_key=gid,
                disposition="CONFIRM",
                reviewer=REVIEWER,
                notes=NOTES,
            )
        after = {
            table: (await session.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()
            for table in PHASE6_TABLES
        }
        if before != after:
            raise RuntimeError(f"Phase 6 count changed: before={before}, after={after}")
        state_after = (
            await session.execute(
                text(
                    "SELECT subject_key, status, disposition FROM md_review_queue_state "
                    "WHERE queue_type=:q AND subject_key = ANY(:keys) ORDER BY subject_key"
                ),
                {"q": QUEUE_P1, "keys": list(TARGETS)},
            )
        ).mappings().all()
        print(json.dumps({
            "database": db,
            "mode": "APPLIED_RECORD_ONLY",
            "targets": list(TARGETS),
            "state_after": [dict(r) for r in state_after],
            "phase6_counts_unchanged": True,
            "production_accessed": False,
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    raise SystemExit(asyncio.run(main(parser.parse_args().apply)))
