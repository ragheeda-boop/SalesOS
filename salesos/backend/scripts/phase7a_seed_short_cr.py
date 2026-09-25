#!/usr/bin/env python3
"""Phase 7-A — Idempotent seed of the 36 suspicious short-CR accounts as PENDING
review items in md_review_queue_state (queue_type='SHORT_CR').

Writes pending rows only: no disposition, no reviewer, no CR change. Adjudication
stays human (report 91 §4.2, gate G3). Source: the G3 review workbook
docs/data/phase6/review/REVIEW_36_SUSPICIOUS_SHORT_CR.csv (report 90).
Aborts if any MA ID does not resolve to exactly one real Global Company.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
import uuid

import asyncpg

QUEUE = "SHORT_CR"
WORKBOOK = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "docs", "data", "phase6", "review",
    "REVIEW_36_SUSPICIOUS_SHORT_CR.csv",
)


async def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else WORKBOOK
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    conn = await asyncpg.connect(host="localhost", port=5432, user="salesos",
                                 password="salesos_dev_password", database="salesos_test")
    try:
        if await conn.fetchval("SELECT current_database()") != "salesos_test":
            print("ABORT: not salesos_test")
            return 2
        seed = []
        for r in rows:
            gids = await conn.fetch(
                "SELECT m.global_entity_id FROM md_legacy_id_mappings m "
                "JOIN md_global_companies g ON g.id = m.global_entity_id "
                "WHERE m.legacy_id_type = 'LEGACY_MUHIDE_MA_ID' AND m.legacy_id = $1",
                r["ma_id"],
            )
            if len(gids) != 1:
                print(f"ABORT: {r['ma_id']} resolves to {len(gids)} companies")
                return 3
            seed.append((
                str(uuid.uuid5(uuid.NAMESPACE_DNS, f"p7a:{QUEUE}:{r['ma_id']}")),
                QUEUE, r["ma_id"], gids[0]["global_entity_id"],
                json.dumps({"cr_raw": r["cr_raw"], "source": "REVIEW_36_SUSPICIOUS_SHORT_CR.csv"},
                           ensure_ascii=False),
            ))
        before = await conn.fetchval("SELECT count(*) FROM md_review_queue_state WHERE queue_type=$1", QUEUE)
        await conn.executemany(
            "INSERT INTO md_review_queue_state (id, queue_type, subject_key, global_company_id, evidence_ref, status) "
            "VALUES ($1::uuid, $2, $3, $4, CAST($5 AS JSONB), 'pending') "
            "ON CONFLICT (queue_type, subject_key) DO NOTHING",
            seed,
        )
        after = await conn.fetchval("SELECT count(*) FROM md_review_queue_state WHERE queue_type=$1", QUEUE)
        decided = await conn.fetchval(
            "SELECT count(*) FROM md_review_queue_state WHERE queue_type=$1 AND disposition IS NOT NULL", QUEUE)
        print(f"SHORT_CR seed: workbook={len(rows)} before={before} after={after} decided={decided}")
        return 0 if after == len(rows) else 1
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
