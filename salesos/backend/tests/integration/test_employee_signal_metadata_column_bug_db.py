"""EmployeeSignalModel maps its "metadata" DB column to the Python
attribute `signal_metadata` (Column("metadata", JSONB, ...)) -- a
deliberate rename, since every SQLAlchemy declarative model class has a
reserved class-level `metadata` attribute (the schema MetaData registry).

PostgresEmployeeSignalRepository.save()/save_many() nonetheless
constructed EmployeeSignalModel(metadata=signal.metadata, ...) -- passing
"metadata" as a keyword argument. SQLAlchemy's declarative __init__ does
not reject this: it silently sets an INSTANCE attribute `model.metadata`
(shadowing the class-level MetaData descriptor for that one object), which
is not mapped to any column. The real `signal_metadata` attribute -- the
one that actually gets INSERTed -- was never touched, so every signal's
metadata was silently discarded on every write, forever, with the DB
column ending up as the model's `default=dict` (empty {}).

Independently, on the READ side, get_by_employee()/get_summary() built
EmployeeSignal(metadata=r.metadata or {}, ...) -- but `r.metadata` on a
row loaded via a real SELECT is the class-level MetaData() singleton
(never None), which is truthy, so the `or {}` fallback never triggers.
Every EmployeeSignal ever reconstructed from the database therefore had
its .metadata field silently set to a SQLAlchemy internal MetaData
object instead of a dict -- a distinct, second-order bug, independent of
the write-side data loss.

The pre-existing tests/employee/tests/test_postgres_repo.py::
test_signal_has_all_required_fields never caught this because it re-reads
the row through the SAME session that performed the save() -- SQLAlchemy's
identity map returns the exact same in-memory (poisoned) Python object,
not a genuine round trip through the database. This file uses two
separate sessions (and a raw SQL read of the actual column) to prove
the real, persisted behavior.

Fixed by using the correct `signal_metadata=` keyword on write and
`r.signal_metadata` on read, in all 4 occurrences.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import apply_tenant_guc, async_session, engine
from domains.employee.models import EmployeeSignal
from domains.employee.postgres_repo import PostgresEmployeeSignalRepository


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    async with engine.connect() as conn:
        db_name = await conn.scalar(text("SELECT current_database()"))
    assert db_name != "salesos", (
        f"REFUSING: connected to {db_name!r} — this is the persistent "
        "local dev database, not a disposable/test one."
    )
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_signal_metadata_survives_a_genuine_round_trip():
    tenant_id = str(uuid.uuid4())
    employee_id = str(uuid.uuid4())
    signal = EmployeeSignal(
        id=str(uuid.uuid4()),
        employee_id=employee_id,
        tenant_id=tenant_id,
        signal_type="deal_assigned",
        source="crm",
        metadata={"deal_id": "123", "important": True},
        timestamp=datetime.now(timezone.utc),
    )

    async with async_session() as s:
        await apply_tenant_guc(s, tenant_id)
        repo = PostgresEmployeeSignalRepository(s)
        await repo.save(signal)
        await s.commit()

    # A genuinely separate session — no identity-map shortcut available.
    async with async_session() as s2:
        await apply_tenant_guc(s2, tenant_id)
        raw = (
            await s2.execute(
                text("SELECT metadata FROM employee_signals WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
        ).first()
        assert raw is not None
        assert raw[0] == {"deal_id": "123", "important": True}, (
            "the raw DB column must contain the real metadata, not {}"
        )

        repo2 = PostgresEmployeeSignalRepository(s2)
        signals, total, _ = await repo2.get_by_employee(employee_id, tenant_id)
        assert total == 1
        assert isinstance(signals[0].metadata, dict), (
            "must be a plain dict, not a SQLAlchemy MetaData() singleton"
        )
        assert signals[0].metadata == {"deal_id": "123", "important": True}


@pytest.mark.asyncio
async def test_save_many_metadata_also_survives_a_genuine_round_trip():
    tenant_id = str(uuid.uuid4())
    employee_id = str(uuid.uuid4())
    signals = [
        EmployeeSignal(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            tenant_id=tenant_id,
            signal_type="email_sent",
            source="crm",
            metadata={"thread_id": f"t-{i}"},
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(3)
    ]

    async with async_session() as s:
        await apply_tenant_guc(s, tenant_id)
        repo = PostgresEmployeeSignalRepository(s)
        await repo.save_many(signals)
        await s.commit()

    async with async_session() as s2:
        await apply_tenant_guc(s2, tenant_id)
        repo2 = PostgresEmployeeSignalRepository(s2)
        result, total, _ = await repo2.get_by_employee(employee_id, tenant_id)
        assert total == 3
        thread_ids = {r.metadata.get("thread_id") for r in result}
        assert thread_ids == {"t-0", "t-1", "t-2"}
