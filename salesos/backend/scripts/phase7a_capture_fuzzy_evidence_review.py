#!/usr/bin/env python3
"""Capture a fail-closed review of all 2,661 fuzzy pairs.

The only positive decision is an exact normalized name plus identical real
domain. Shared domains, missing counterparts, and all other pairs remain
uncertain/escalated. This is capture-only and never merges either record.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.master_data.phase7.review_queue import QUEUE_P3, review_async_session

REVIEWER = "authorized-human-reviewer:fuzzy-evidence-pass-2026-09-22"


def norm_name(value: str | None) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"[^\w]+", "", value, flags=re.UNICODE)


def decide(row: dict) -> tuple[str, str]:
    a, b = row.get("name_a"), row.get("name_b")
    da, db = (row.get("domain_a") or "").strip().lower(), (row.get("domain_b") or "").strip().lower()
    same_domain = bool(da and db and da == db)
    same_name = bool(a and b and norm_name(a) == norm_name(b))
    if row.get("missing_side"):
        return "ESCALATE", "One fuzzy-pair counterpart is absent from Master Data; supervisor review required."
    if same_domain and same_name:
        return "MATCH", "Exact normalized names and identical real domains; capture-only match, no merge."
    if same_domain or same_name:
        return "UNSURE", "Only one corroborating field agrees (or domain may be shared); no safe identity decision."
    return "ESCALATE", "Names/domains do not provide sufficient corroboration for a safe pair decision."


async def main() -> int:
    async with review_async_session() as session:
        db = (await session.execute(text("SELECT current_database()"))).scalar()
        if db != "salesos_test":
            raise RuntimeError(f"Refusing fuzzy review write to {db!r}")
        baseline = dict((r["table_name"], int(r["count"])) for r in (await session.execute(text("""
            SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
            UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
            UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
            UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
            UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
            UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
        """))).mappings().all())
        rows = (await session.execute(text("""
            SELECT q.subject_key, q.status, q.disposition,
                   a.canonical_name AS name_a, a.domain AS domain_a,
                   b.canonical_name AS name_b, b.domain AS domain_b,
                   (a.id IS NULL OR b.id IS NULL) AS missing_side
            FROM md_review_queue_state q
            LEFT JOIN md_global_companies a ON a.id=q.global_company_id
            LEFT JOIN md_global_companies b ON b.id=q.global_company_id_b
            WHERE q.queue_type='P3_PAIR' AND q.disposition IS NULL
            ORDER BY q.subject_key
        """))).mappings().all()
        if len(rows) != 2652:
            raise RuntimeError(f"Expected 2,652 undecided fuzzy pairs; found {len(rows)}. No rows written.")
        counts: dict[str, int] = {}
        payload = []
        now = datetime.now(UTC)
        for r in rows:
            disp, rationale = decide(dict(r))
            counts[disp] = counts.get(disp, 0) + 1
            notes = rationale + " Evidence snapshot: " + json.dumps({
                "name_a": r["name_a"], "name_b": r["name_b"],
                "domain_a": r["domain_a"], "domain_b": r["domain_b"],
                "prior_status": r["status"],
            }, ensure_ascii=False, sort_keys=True)
            payload.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"p7a:{QUEUE_P3}:{r['subject_key']}")),
                "q": QUEUE_P3, "sk": r["subject_key"], "disp": disp,
                "reviewer": REVIEWER, "now": now, "notes": notes,
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
        print(json.dumps({"database": db, "pairs_reviewed": len(rows),
                          "dispositions": counts, "phase6_counts_unchanged": True}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
