#!/usr/bin/env python3
"""Stage the authorized MA v1.0 decisions without canonical Master Data writes."""

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
from app.modules.master_data.phase7.review_queue import review_async_session

MANIFEST = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v1.0.csv")
REVIEWER = "authorized-human-reviewer:phase7-gate-2026-09-22"
APPLIED_STATUSES = {
    "RESOLVED_VIA_EXACT_NAME_DOMAIN_MASTER_V10",
    "RESOLVED_VIA_APOLLO_ACCOUNT_ID_MASTER_CORROBORATION",
    "RESOLVED_VIA_APOLLO_AND_EXACT_NAME_DOMAIN",
}


async def main() -> int:
    manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    rows = []
    with MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            status = (row.get("Linkage_Status") or "").strip()
            if status in APPLIED_STATUSES or status == "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW":
                rows.append(row)
    if len(rows) != 1_114 or len({r.get("global_person_id") for r in rows}) != 1_114:
        raise RuntimeError("Expected the 1,114 MA-unresolved source keys")
    applied = [r for r in rows if (r.get("Linkage_Status") or "") in APPLIED_STATUSES]
    escalated = [r for r in rows if (r.get("Linkage_Status") or "") not in APPLIED_STATUSES]
    if len(applied) != 792 or len(escalated) != 322:
        raise RuntimeError(f"Unexpected v1.0 decision counts: {len(applied)} / {len(escalated)}")
    for row in applied:
        try:
            uuid.UUID(row["Global_Company_ID"])
        except (ValueError, TypeError):
            raise RuntimeError(f"Non-UUID company proposal for {row['global_person_id']}")

    async with review_async_session() as session:
        if (await session.execute(text("SELECT current_database()"))).scalar() != "salesos_test":
            raise RuntimeError("Refusing proposal staging outside salesos_test")
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS md_person_company_link_proposals (
                id UUID PRIMARY KEY,
                source_person_key VARCHAR(128) NOT NULL UNIQUE,
                proposed_company_id UUID NULL,
                status VARCHAR(24) NOT NULL,
                match_method VARCHAR(96) NOT NULL,
                evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
                manifest_sha256 VARCHAR(64) NOT NULL,
                reviewer VARCHAR(255) NOT NULL,
                approved_at TIMESTAMPTZ NOT NULL,
                applied_person_id UUID NULL,
                applied_at TIMESTAMPTZ NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_md_person_company_link_proposals_status ON md_person_company_link_proposals (status)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_md_person_company_link_proposals_company ON md_person_company_link_proposals (proposed_company_id)"))
        baseline = dict((r["table_name"], int(r["count"])) for r in (await session.execute(text("""
            SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
            UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
            UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
            UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
            UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
            UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
        """))).mappings().all())
        now = datetime.now(UTC)
        payload = []
        for row in rows:
            status = (row.get("Linkage_Status") or "").strip()
            is_applied = status in APPLIED_STATUSES
            payload.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"salesos:ma-proposal:{row['global_person_id']}")),
                "key": row["global_person_id"],
                "company": row.get("Global_Company_ID") if is_applied else None,
                "status": "PROPOSED" if is_applied else "ESCALATED",
                "method": status,
                "evidence": json.dumps({
                    "source_id": "muhide_contacts_v07",
                    "linkage_status": status,
                    "global_person_id": row["global_person_id"],
                    "organization_raw": row.get("organization_raw") or "",
                    "apollo_account_id": row.get("apollo_account_id") or "",
                    "manifest": "03_Master_Contacts_FINAL_v1.0.csv",
                }, ensure_ascii=False),
                "manifest": manifest_sha,
                "reviewer": REVIEWER,
                "now": now,
            })
        await session.execute(text("""
            INSERT INTO md_person_company_link_proposals
              (id, source_person_key, proposed_company_id, status, match_method, evidence,
               manifest_sha256, reviewer, approved_at)
            VALUES (:id, :key, CAST(:company AS uuid), :status, :method, CAST(:evidence AS jsonb),
                    :manifest, :reviewer, :now)
            ON CONFLICT (source_person_key) DO UPDATE SET
              proposed_company_id=EXCLUDED.proposed_company_id,
              status=EXCLUDED.status,
              match_method=EXCLUDED.match_method,
              evidence=EXCLUDED.evidence,
              manifest_sha256=EXCLUDED.manifest_sha256,
              reviewer=EXCLUDED.reviewer,
              approved_at=EXCLUDED.approved_at,
              updated_at=now()
        """), payload)
        after = dict((r["table_name"], int(r["count"])) for r in (await session.execute(text("""
            SELECT 'md_global_companies' AS table_name, COUNT(*) AS count FROM md_global_companies
            UNION ALL SELECT 'md_global_people', COUNT(*) FROM md_global_people
            UNION ALL SELECT 'md_source_rows', COUNT(*) FROM md_source_rows
            UNION ALL SELECT 'md_identity_classifications', COUNT(*) FROM md_identity_classifications
            UNION ALL SELECT 'md_sales_readiness_history', COUNT(*) FROM md_sales_readiness_history
            UNION ALL SELECT 'md_review_candidates', COUNT(*) FROM md_review_candidates
        """))).mappings().all())
        if baseline != after:
            raise RuntimeError(f"Canonical Phase 6 count drift: before={baseline}, after={after}")
        result = (await session.execute(text("""
            SELECT status, COUNT(*) AS count FROM md_person_company_link_proposals
            GROUP BY status ORDER BY status
        """))).all()
        await session.commit()
        print(json.dumps({
            "database": "salesos_test",
            "manifest_sha256": manifest_sha,
            "staged": len(rows),
            "statuses": {str(k): int(v) for k, v in result},
            "canonical_phase6_unchanged": True,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
