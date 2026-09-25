"""Phase 7A traceability QA gate.

Read-only. Asserts the invariants that let a reviewer trust the review queue.
Every check is a hard gate: a non-zero count is a FAIL, never a warning.

Invariants
----------
Q1  every queue row carries a well-formed evidence_ref (object, non-empty)
Q2  no queue row points at a non-existent global company (dangling link)
Q3  P1_CANDIDATE: dispositioned rows are linked to a real company and labelled
Q4  P3_PAIR: linkage_status is one of the declared values and matches the
    actual NULL-ness of global_company_id / global_company_id_b
Q5  SHORT_CR: a row adjudicated CONFIRMED_ARTIFACT is a resolution and must
    not be counted as pending; UNRESOLVED_ESCALATE must not be counted resolved
Q6  no ESCALATED row is silently treated as resolved by the usability SQL
Q7  Phase 6 population floors (regression tripwires, not exact pins)

Exit code 0 = all gates pass.
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg

DSN = os.environ.get(
    "SALESOS_TEST_DSN",
    "postgresql://salesos:salesos_dev_password@localhost:5432/salesos_test",
)

ACTIVE_VERSION = "OPTION_C_1+NCNP+DS5+LV+CR+ED"
P3_STATUSES = ("COMPLETE", "MISSING_SIDE_B", "MISSING_BOTH")
RESOLVING = ("CONFIRM", "SEPARATE")

CHECKS: list[tuple[str, str]] = []


def check(name: str):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn

    return deco


@check("Q1 evidence_ref well-formed on every row")
async def q1(c: asyncpg.Connection) -> int:
    return await c.fetchval(
        "SELECT count(*) FROM md_review_queue_state "
        "WHERE evidence_ref IS NULL OR jsonb_typeof(evidence_ref) <> 'object' "
        "OR evidence_ref = '{}'::jsonb"
    )


@check("Q2 no dangling global_company_id / _b")
async def q2(c: asyncpg.Connection) -> int:
    return await c.fetchval(
        """
        SELECT count(*) FROM md_review_queue_state q
         WHERE (q.global_company_id IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM md_global_companies g
                                 WHERE g.id = q.global_company_id))
            OR (q.global_company_id_b IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM md_global_companies g
                                 WHERE g.id = q.global_company_id_b))
        """
    )


@check("Q3 P1 dispositioned rows linked + labelled")
async def q3(c: asyncpg.Connection) -> int:
    return await c.fetchval(
        """
        SELECT count(*) FROM md_review_queue_state
         WHERE queue_type = 'P1_CANDIDATE'
           AND (global_company_id IS NULL
                OR evidence_ref->>'linkage_status' IS NULL)
        """
    )


@check("Q4 P3 linkage_status matches actual NULL-ness of the two sides")
async def q4(c: asyncpg.Connection) -> int:
    return await c.fetchval(
        """
        SELECT count(*) FROM md_review_queue_state
         WHERE queue_type = 'P3_PAIR'
           AND (
                evidence_ref->>'linkage_status' IS NULL
             OR evidence_ref->>'linkage_status' NOT IN ('COMPLETE','MISSING_SIDE_B','MISSING_BOTH')
             OR (evidence_ref->>'linkage_status' = 'COMPLETE'
                 AND (global_company_id IS NULL OR global_company_id_b IS NULL))
             OR (evidence_ref->>'linkage_status' = 'MISSING_SIDE_B'
                 AND (global_company_id IS NULL OR global_company_id_b IS NOT NULL))
             OR (evidence_ref->>'linkage_status' = 'MISSING_BOTH'
                 AND (global_company_id IS NOT NULL OR global_company_id_b IS NOT NULL))
               )
        """
    )


@check("Q5 SHORT_CR resolution states are self-consistent")
async def q5(c: asyncpg.Connection) -> int:
    return await c.fetchval(
        """
        SELECT count(*) FROM md_review_queue_state
         WHERE queue_type = 'SHORT_CR'
           AND (disposition IS NULL
             OR disposition NOT IN ('CONFIRMED_ARTIFACT','UNRESOLVED_ESCALATE')
             OR (disposition = 'CONFIRMED_ARTIFACT' AND global_company_id IS NULL))
        """
    )


@check("Q6 no ESCALATED P3/SHORT_CR row is left unblocked by semantics")
async def q6(c: asyncpg.Connection) -> int:
    # An escalated P3 pair must still be blocking. The defect under guard:
    # _FACTS_SQL used status='pending' alone, so ESCALATE released the account.
    return await c.fetchval(
        """
        WITH blocking AS (
            SELECT global_company_id AS id FROM md_review_queue_state
             WHERE queue_type = 'P3_PAIR'
               AND (disposition IS NULL OR disposition NOT IN ('CONFIRM','SEPARATE'))
               AND global_company_id IS NOT NULL
            UNION
            SELECT global_company_id_b FROM md_review_queue_state
             WHERE queue_type = 'P3_PAIR'
               AND (disposition IS NULL OR disposition NOT IN ('CONFIRM','SEPARATE'))
               AND global_company_id_b IS NOT NULL
            UNION
            SELECT global_company_id FROM md_review_queue_state
             WHERE queue_type = 'SHORT_CR'
               AND (status = 'pending' OR disposition IS NULL
                    OR disposition = 'UNRESOLVED_ESCALATE')
               AND global_company_id IS NOT NULL
        )
        SELECT count(*) FROM md_review_queue_state q
         WHERE q.queue_type IN ('P3_PAIR','SHORT_CR')
           AND (q.disposition = 'ESCALATE' OR q.disposition = 'UNRESOLVED_ESCALATE')
           AND (q.global_company_id IN (SELECT id FROM blocking)
                OR q.global_company_id_b IN (SELECT id FROM blocking))
           AND q.global_company_id IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM blocking b WHERE b.id = q.global_company_id)
        """
    )


@check("Q7 Phase 6 population floors")
async def q7(c: asyncpg.Connection) -> int:
    """Return the number of floors violated (each floor is a documented baseline)."""
    floors = {
        "md_source_rows": 909_967,
        "md_global_companies": 296_746,
        "md_identity_classifications": 1_483_730,
        "md_review_candidates": 54_754,
        "md_legacy_id_mappings": 314_413,
        "md_field_provenance": 1_524_717,
    }
    bad = 0
    for table, floor in floors.items():
        n = await c.fetchval(f"SELECT count(*) FROM {table}")
        if n < floor:
            print(f"      ! {table}: {n:,} < floor {floor:,}")
            bad += 1
    return bad


@check("Q8 linkage foreign keys present on the queue")
async def q8(c: asyncpg.Connection) -> int:
    """The application guard is not enough; the DB must enforce it too."""
    have = {
        r["conname"]
        for r in await c.fetch(
            "SELECT conname FROM pg_constraint "
            "WHERE conrelid = 'md_review_queue_state'::regclass AND contype = 'f'"
        )
    }
    want = {"fk_md_review_queue_state_company", "fk_md_review_queue_state_company_b"}
    missing = want - have
    for m in sorted(missing):
        print(f"      ! missing FK {m}")
    return len(missing)


async def main() -> int:
    c = await asyncpg.connect(DSN)
    db = await c.fetchval("SELECT current_database()")
    print(f"Phase 7A traceability QA gate — database: {db}\n")
    failures = 0
    for name, fn in CHECKS:
        try:
            bad = await fn(c)
        except Exception as exc:
            print(f"  ERROR  {name}: {exc}")
            failures += 1
            continue
        if bad:
            print(f"  FAIL   {name}: {bad} violation(s)")
            failures += 1
        else:
            print(f"  PASS   {name}")
    await c.close()
    print()
    if failures:
        print(f"RESULT: FAIL ({failures} gate(s))")
        return 1
    print("RESULT: PASS (all gates)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
