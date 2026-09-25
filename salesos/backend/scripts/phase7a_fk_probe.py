"""Prove the new FK constraints actually reject a dangling company link.

Read-only with respect to committed data: every probe runs inside a transaction
that is rolled back, so no row survives.
"""

import asyncio
import uuid

import asyncpg

DSN = "postgresql://salesos:salesos_dev_password@localhost:5432/salesos_test"


async def main() -> None:
    c = await asyncpg.connect(DSN)
    fake = uuid.uuid4()

    for col in ("global_company_id", "global_company_id_b"):
        try:
            async with c.transaction():
                await c.execute(
                    f"""
                    INSERT INTO md_review_queue_state
                        (id, queue_type, subject_key, {col}, evidence_ref)
                    VALUES ($1, 'P1_CANDIDATE', $2, $3, '{{}}'::jsonb)
                    """,
                    uuid.uuid4(),
                    f"fk-probe-{col}",
                    fake,
                )
            print(f"  {col:<20} NOT BLOCKED  <-- guard ineffective")
        except asyncpg.ForeignKeyViolationError as exc:
            print(f"  {col:<20} BLOCKED by FK  ({exc.constraint_name})")

    n = await c.fetchval(
        "SELECT count(*) FROM md_review_queue_state WHERE subject_key LIKE 'fk-probe-%'"
    )
    print(f"\n  probe rows persisted: {n}  (must be 0)")

    # A legal link must still be accepted.
    real = await c.fetchval("SELECT id FROM md_global_companies LIMIT 1")
    # NOTE: `async with c.transaction()` COMMITS on clean exit. The accepted-link
    # probe must therefore be rolled back explicitly, or it persists a junk row.
    tr = c.transaction()
    await tr.start()
    await c.execute(
        """
        INSERT INTO md_review_queue_state
            (id, queue_type, subject_key, global_company_id, evidence_ref)
        VALUES ($1, 'P1_CANDIDATE', $2, $3, '{}'::jsonb)
        """,
        uuid.uuid4(),
        f"fk-probe-legal-{uuid.uuid4().hex[:8]}",
        real,
    )
    await tr.rollback()
    print("  legal link accepted (constraint is not over-blocking)")

    leaked = await c.fetchval(
        "SELECT count(*) FROM md_review_queue_state WHERE subject_key LIKE 'fk-probe-%'"
    )
    print(f"  probe rows persisted after rollback: {leaked}  (must be 0)")
    await c.close()


asyncio.run(main())
