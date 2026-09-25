#!/usr/bin/env python3
"""Capture the conservative, authorized P1 evidence review.

The pass reviews every pending P1 candidate using the Phase 6 evidence that is
already stored on the candidate.  It is deliberately fail-closed:

* domain/CR conflicts are escalated;
* only a ``MATCHED`` result with a real domain is confirmed;
* likely matches and weak identity evidence remain ``REVIEW`` or ``ESCALATE``.

This writes only disposition state to ``md_review_queue_state`` in
``salesos_test``.  It never changes a candidate, identity, readiness, source
row, Global ID, or production database.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.master_data.phase7.review_queue import (
    QUEUE_P1,
    review_async_session,
)

REVIEWER = "authorized-human-reviewer:p1-evidence-pass-2026-09-22"


def decide(reason: str, evidence: dict) -> tuple[str, str]:
    conflict_fields = evidence.get("conflict_fields") or []
    if reason == "FIELD_CONFLICT_REVIEW" or conflict_fields:
        return "ESCALATE", "Conflicting identity field(s) require data-owner adjudication; no merge or field change."
    if reason == "CORROBORATION_REVIEW":
        matched = evidence.get("best_match_confidence") == "MATCHED"
        real_domain = bool(evidence.get("real_domain_present"))
        if matched and real_domain:
            return "CONFIRM", "Evidence review: MATCHED with a real domain; capture-only confirmation, no merge or data mutation."
        return "REVIEW", "Evidence is plausible but not strong enough for confirmation; retain for second review."
    # Weak identity has no corroborating CR/ER match by contract.
    return "ESCALATE", "Weak or ambiguous identity evidence; escalate to data owner rather than infer identity."


async def main() -> int:
    async with review_async_session() as session:
        db = (await session.execute(text("SELECT current_database()"))).scalar()
        if db != "salesos_test":
            raise RuntimeError(f"Refusing P1 review write to {db!r}")
        baseline = dict((r["table_name"], int(r["count"])) for r in (await session.execute(text("""
            SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
            UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
            UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
            UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
            UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
            UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
        """))).mappings().all())
        rows = (await session.execute(text("""
            SELECT rc.global_entity_id::text AS gid, rc.reason, rc.evidence
            FROM md_review_candidates rc
            LEFT JOIN md_review_queue_state q
              ON q.queue_type = 'P1_CANDIDATE' AND q.subject_key = rc.global_entity_id::text
            WHERE rc.candidate_type = 'P1' AND rc.status = 'pending' AND rc.decision IS NULL
              AND q.id IS NULL
            ORDER BY rc.global_entity_id
        """))).mappings().all()
        counts: dict[str, int] = {}
        payload = []
        now = datetime.now(UTC)
        for row in rows:
            evidence = row["evidence"] if isinstance(row["evidence"], dict) else json.loads(row["evidence"] or "{}")
            disposition, rationale = decide(row["reason"], evidence)
            counts[disposition] = counts.get(disposition, 0) + 1
            payload.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"p7a:{QUEUE_P1}:{row['gid']}")),
                "q": QUEUE_P1, "sk": row["gid"], "disp": disposition,
                "reviewer": REVIEWER, "now": now,
                "notes": rationale + " Evidence snapshot: " + json.dumps({
                    "reason": row["reason"],
                    "best_match_confidence": evidence.get("best_match_confidence"),
                    "real_domain_present": evidence.get("real_domain_present"),
                    "apollo_account_present": evidence.get("apollo_account_present"),
                    "cr_class": evidence.get("cr_class"),
                    "conflict_fields": evidence.get("conflict_fields"),
                }, sort_keys=True),
            })
        if len(payload) != 6904:
            raise RuntimeError(f"Expected 6,904 pending P1 candidates; found {len(payload)}. No rows written.")
        await session.execute(text("""
            INSERT INTO md_review_queue_state
              (id, queue_type, subject_key, status, disposition, reviewer, reviewed_at, notes)
            VALUES (:id, :q, :sk, 'dispositioned', :disp, :reviewer, :now, :notes)
            ON CONFLICT (queue_type, subject_key) DO UPDATE
              SET status='dispositioned', disposition=:disp, reviewer=:reviewer,
                  reviewed_at=:now, notes=:notes
        """), payload)
        await session.commit()
        after = dict((r["table_name"], int(r["count"])) for r in (await session.execute(text("""
            SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
            UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
            UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
            UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
            UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
            UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
        """))).mappings().all())
        if baseline != after:
            raise RuntimeError(f"Safety failure: Phase 6 counts changed: before={baseline}, after={after}")
        print(json.dumps({"database": db, "pending_reviewed": len(payload),
                          "dispositions": counts, "phase6_counts_unchanged": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
