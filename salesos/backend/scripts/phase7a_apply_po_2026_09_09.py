#!/usr/bin/env python3
"""Phase 7-A — Apply the 2026-09-09 PO capture-only decisions.

Authority: docs/data/phase7/PHASE7A_PO_DECISION_2026-09-09.md

Writes ONLY md_review_queue_state on salesos_test:
  D1  9 P3 pairs           -> SEPARATE via ReviewQueueService.record_disposition
  D2  ~1763 missing-B rows -> status=deferred_engineering (not a MATCH/SEPARATE)
  D3a ~114 domain-equal    -> notes stamp only; disposition stays NULL (review batch)
  D3b 4 P1 CR-conflicts    -> TRIAGE CONFIRM via record_disposition

No merge, no CR promotion, no Phase 6 table write, no production.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.modules.master_data.phase7.review_queue import ReviewQueueService

PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_URL = f"postgresql+asyncpg://salesos:salesos_dev_password@{PG_HOST}:5432/salesos_test"

REVIEWER = "Ragheb (PO)"
DECISION_REF = "PHASE7A_PO_DECISION_2026-09-09"

SEPARATE_KEYS = [
    "286401:286407",
    "287268:287970",
    "288401:298731",
    "290347:290348",
    "292483:292518",
    "299671:299673",
    "303251:303254",
    "303251:303255",
    "303254:303255",
]

P1_CONFIRM_MAS = [
    "MA-0259345",
    "MA-0263479",
    "MA-0269017",
    "MA-0272304",
]

NOTE_SEPARATE = (
    f"{DECISION_REF} D1: PO rule SEPARATE_ALL — different CR = distinct legal entity. "
    "Record-only; no merge."
)
NOTE_DEFERRED = (
    f"{DECISION_REF} D2: missing counterpart (global_company_id_b NULL). "
    "Not a reviewer task; routed to engineering."
)
NOTE_PRIORITY = (
    f"{DECISION_REF} D3: first HIGH_MATCH human-review batch (domain-equal). "
    "Disposition pending human review — not auto-MATCH."
)
NOTE_CONFIRM = (
    f"{DECISION_REF} D3: CONFIRM — same account already Short-CR CONFIRMED_ARTIFACT. "
    "Record-only; no classification change."
)


async def main(dry_run: bool) -> int:
    engine = create_async_engine(PG_URL)
    async with AsyncSession(engine) as session:
        svc = ReviewQueueService(session=session)
        await svc._assert_write_db()

        before = await _snapshot(session)
        print(f"DB=salesos_test  dry_run={dry_run}")
        print(f"before: {before}")

        # D1 — SEPARATE the 9
        separate_ok = 0
        for sk in SEPARATE_KEYS:
            exists = await session.execute(
                text(
                    "SELECT 1 FROM md_review_queue_state "
                    "WHERE queue_type='P3_PAIR' AND subject_key=:sk"
                ),
                {"sk": sk},
            )
            if exists.scalar() is None:
                print(f"  MISSING P3 pair {sk}")
                continue
            separate_ok += 1
            if dry_run:
                print(f"  DRY-RUN P3 {sk} -> SEPARATE")
                continue
            await svc.record_disposition(
                queue_type="P3_PAIR",
                subject_key=sk,
                disposition="SEPARATE",
                reviewer=REVIEWER,
                notes=NOTE_SEPARATE,
            )
        print(f"D1 SEPARATE targets found: {separate_ok}/9")

        # D3b — CONFIRM four P1 CR-conflict accounts
        confirm_ok = 0
        for ma in P1_CONFIRM_MAS:
            row = await session.execute(
                text(
                    "SELECT lm.global_entity_id::text AS gid "
                    "FROM md_legacy_id_mappings lm "
                    "WHERE lm.legacy_id_type='LEGACY_MUHIDE_MA_ID' AND lm.legacy_id=:ma"
                ),
                {"ma": ma},
            )
            gid = row.scalar()
            if not gid:
                print(f"  MISSING mapping for {ma}")
                continue
            confirm_ok += 1
            if dry_run:
                print(f"  DRY-RUN TRIAGE {ma} ({gid}) -> CONFIRM")
                continue
            await svc.record_disposition(
                queue_type="TRIAGE",
                subject_key=gid,
                disposition="CONFIRM",
                reviewer=REVIEWER,
                notes=NOTE_CONFIRM,
            )
        print(f"D3b TRIAGE CONFIRM targets found: {confirm_ok}/4")

        # D3a — stamp 114 domain-equal pending pairs (no disposition)
        exclude_sql = ", ".join(f"'{k}'" for k in SEPARATE_KEYS)
        domain_sql = text(
            f"""
            SELECT q.subject_key
            FROM md_review_queue_state q
            JOIN md_global_companies a ON a.id = q.global_company_id
            JOIN md_global_companies b ON b.id = q.global_company_id_b
            WHERE q.queue_type = 'P3_PAIR'
              AND q.global_company_id_b IS NOT NULL
              AND q.subject_key NOT IN ({exclude_sql})
              AND a.domain IS NOT NULL AND btrim(a.domain) <> ''
              AND lower(btrim(a.domain)) = lower(btrim(b.domain))
            """
        )
        domain_rows = await session.execute(domain_sql)
        domain_keys = [r[0] for r in domain_rows.all()]
        print(f"D3a domain-equal pairs: {len(domain_keys)} (expect ~114)")
        if not dry_run and domain_keys:
            for sk in domain_keys:
                await session.execute(
                    text(
                        "UPDATE md_review_queue_state SET notes = :n "
                        "WHERE queue_type='P3_PAIR' AND subject_key = :sk "
                        "AND disposition IS NULL"
                    ),
                    {"n": NOTE_PRIORITY, "sk": sk},
                )
            await session.commit()

        # D2 — defer missing-counterpart pairs
        missing = await session.execute(
            text(
                "SELECT COUNT(*) FROM md_review_queue_state "
                "WHERE queue_type='P3_PAIR' AND global_company_id_b IS NULL"
            )
        )
        missing_n = int(missing.scalar() or 0)
        print(f"D2 missing-counterpart pairs: {missing_n} (expect ~1763)")
        if not dry_run:
            await session.execute(
                text(
                    "UPDATE md_review_queue_state "
                    "SET status='deferred_engineering', notes=:n, "
                    "    reviewer=:r, reviewed_at=NOW() "
                    "WHERE queue_type='P3_PAIR' AND global_company_id_b IS NULL "
                    "AND disposition IS NULL"
                ),
                {"n": NOTE_DEFERRED, "r": REVIEWER},
            )
            await session.commit()

        after = await _snapshot(session)
        print(f"after: {after}")
        for tbl, n in after["phase6"].items():
            if n != before["phase6"][tbl]:
                print(f"REFUSING SAFETY: {tbl} changed {before['phase6'][tbl]} -> {n}")
                return 3

        if dry_run:
            print("DRY RUN — no rows were written.")
        else:
            print("Writes committed to md_review_queue_state only.")
    await engine.dispose()
    return 0


async def _snapshot(session: AsyncSession) -> dict:
    q = await session.execute(
        text(
            """
            SELECT
              COUNT(*) FILTER (WHERE queue_type='P3_PAIR') AS p3,
              COUNT(*) FILTER (WHERE queue_type='P3_PAIR' AND disposition='SEPARATE') AS p3_sep,
              COUNT(*) FILTER (WHERE queue_type='P3_PAIR' AND status='deferred_engineering') AS p3_def,
              COUNT(*) FILTER (WHERE queue_type='TRIAGE' AND disposition='CONFIRM') AS tri_c
            FROM md_review_queue_state
            """
        )
    )
    m = q.mappings().first()
    phase6 = {}
    for tbl in (
        "md_global_companies",
        "md_identity_classifications",
        "md_source_rows",
        "md_review_candidates",
        "md_entity_matches",
        "md_entity_merge_history",
    ):
        n = await session.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
        phase6[tbl] = int(n.scalar() or 0)
    return {
        "p3": m["p3"],
        "p3_separate": m["p3_sep"],
        "p3_deferred": m["p3_def"],
        "triage_confirm": m["tri_c"],
        "phase6": phase6,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.dry_run)))
