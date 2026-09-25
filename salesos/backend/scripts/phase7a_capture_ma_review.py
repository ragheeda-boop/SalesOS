#!/usr/bin/env python3
"""Capture all 1,114 MA-v0.7 review outcomes without applying mappings."""

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

MANIFEST = Path(r"D:\AISalesOS\project-audit\41_MA_UNRESOLVED_HUMAN_REVIEW_2026-09-22.csv")
REVIEWER = "authorized-human-reviewer:ma-v08-proposal-2026-09-22"


def disposition(status: str) -> str:
    if status == "DETERMINISTIC_EXACT_NAME_DOMAIN":
        return "CONFIRM_EXACT"
    if status in {"REVIEW_UNIQUE_DOMAIN", "REVIEW_UNIQUE_NAME"}:
        return "REVIEW"
    return "ESCALATE"


async def main() -> int:
    manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig", newline="")))
    if len(rows) != 1114 or len({r.get("global_person_id") for r in rows}) != 1114:
        raise RuntimeError("Expected 1,114 unique v0.7 contacts in MA manifest")
    async with review_async_session() as session:
        if (await session.execute(text("SELECT current_database()"))).scalar() != "salesos_test":
            raise RuntimeError("Refusing MA review write outside salesos_test")
        baseline = dict((r["table_name"], int(r["count"])) for r in (await session.execute(text("""
            SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
            UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
            UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
            UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
            UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
            UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
        """))).mappings().all())
        source_count = (await session.execute(text("""
            SELECT COUNT(*) FROM md_source_rows
            WHERE source_id='muhide_contacts_v07' AND source_record_id = ANY(:ids)
        """), {"ids": [r["global_person_id"] for r in rows]})).scalar()
        if source_count != 1114:
            raise RuntimeError(f"v0.7 source row validation failed: {source_count}")
        now = datetime.now(UTC)
        payload = []
        counts: dict[str, int] = {}
        for row in rows:
            disp = disposition(row["candidate_status"])
            counts[disp] = counts.get(disp, 0) + 1
            note = (
                f"MA v0.8 proposal review; source manifest SHA-256={manifest_sha}. "
                f"Candidate status={row['candidate_status']}; candidate Global Company ID="
                f"{row.get('candidate_global_company_id') or 'none'}. "
                "Capture-only: no Global ID write, no merge, no production."
            )
            payload.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"p7a:{QUEUE_MA_UNRESOLVED}:{row['global_person_id']}")),
                "q": QUEUE_MA_UNRESOLVED, "sk": row["global_person_id"], "disp": disp,
                "reviewer": REVIEWER, "now": now, "notes": note,
            })
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
        print(json.dumps({"database": "salesos_test", "rows_captured": len(rows),
                          "dispositions": counts, "phase6_counts_unchanged": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
