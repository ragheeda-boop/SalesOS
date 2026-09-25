#!/usr/bin/env python3
"""Refresh MA_UNRESOLVED capture state with the Apollo evidence pass."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.modules.master_data.phase7.review_queue import QUEUE_MA_UNRESOLVED, review_async_session

MANIFEST = Path(r"D:\AISalesOS\project-audit\45_MA_APOLLO_PASS_2026-09-22.csv")
REVIEWER = "authorized-human-reviewer:ma-apollo-pass-2026-09-22"


def disposition(status: str) -> str:
    return "CONFIRM_EXACT" if status == "APOLLO_UNIQUE_MA_CONSISTENT" else "REVIEW" if status == "REVIEW_NO_APOLLO_MATCH" else "ESCALATE"


async def main() -> int:
    manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig", newline="")))
    if len(rows) != 702 or len({r["global_person_id"] for r in rows}) != 702:
        raise RuntimeError("Expected 702 unique rows in Apollo pass manifest")
    async with review_async_session() as session:
        if (await session.execute(text("SELECT current_database()"))).scalar() != "salesos_test":
            raise RuntimeError("Refusing MA Apollo capture outside salesos_test")
        baseline = dict((r["table_name"], int(r["count"])) for r in (await session.execute(text("""
            SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
            UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
            UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
            UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
            UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
            UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
        """))).mappings().all())
        now = datetime.now(UTC); counts = {}; payload = []
        for row in rows:
            disp = disposition(row["apollo_pass_status"]); counts[disp] = counts.get(disp, 0) + 1
            notes = (
                f"Apollo evidence pass; manifest SHA-256={manifest_sha}; status={row['apollo_pass_status']}; "
                f"candidate Global Company ID={row.get('candidate_global_company_id') or 'none'}. "
                "Capture-only; derived v0.9 only, no database/production mapping."
            )
            payload.append({"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"p7a:{QUEUE_MA_UNRESOLVED}:{row['global_person_id']}")),
                            "q": QUEUE_MA_UNRESOLVED, "sk": row["global_person_id"], "disp": disp,
                            "reviewer": REVIEWER, "now": now, "notes": notes})
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
            raise RuntimeError(f"Phase 6 count drift: before={baseline}, after={after}")
        print(json.dumps({"database": "salesos_test", "rows_refreshed": len(rows), "dispositions": counts,
                          "phase6_counts_unchanged": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
