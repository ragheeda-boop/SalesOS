"""Database proof for durable GTM capability results (STORY-11-02..09).

Proves real Postgres persistence + RLS + FORCE RLS on gtm_capability_results
(migration s9t0u1v2w3x4): per-tenant writes/reads, schema_version bumps,
cross-tenant id reuse blocked, sequencing definition/enrollment round-trip,
and that an unpinned or other-tenant session sees zero rows. Only test
databases, via the restricted salesos_app runtime role.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine, owner_engine
from app.modules.gtm.durable_store import (
    DEFINITION_CAPABILITY,
    PostgresGtmStore,
)
from app.modules.gtm.sequencing import SequencingError


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()
    await owner_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_gtm_table():
    # Fixed result ids (e.g. "qa-recompute-1") live in the capability-global
    # primary key, so each test starts from an empty gtm_capability_results to
    # stay hermetic across pytest runs against a shared pool database.
    async with owner_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE gtm_capability_results"))
    yield


async def _set_tenant(session, tenant_id: str | None) -> None:
    if tenant_id:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    else:
        await session.execute(text("RESET app.tenant_id"))


@pytest.mark.asyncio
async def test_capability_results_persist_and_are_tenant_scoped():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    store = PostgresGtmStore(capability="market_sizing")

    snap = await store.compute(
        tenant_id=tenant_a,
        name="QA TAM/SAM/SOM",
        industries=["technology"],
        cities=["riyadh"],
    )
    record = snap.as_dict()
    assert record["tenant_id"] == tenant_a
    assert record["name"] == "QA TAM/SAM/SOM"
    assert 0 <= record["som"] <= record["sam"] <= record["tam"] <= record["universe_size"]

    fetched = await store.get(record["id"], tenant_id=tenant_a)
    assert fetched is not None
    assert fetched.as_dict()["tam"] == record["tam"]

    assert await store.get(record["id"], tenant_id=tenant_b) is None
    assert await store.list_for_tenant(tenant_id=tenant_b) == []
    visible = await store.list_for_tenant(tenant_id=tenant_a)
    assert [r.as_dict()["id"] for r in visible] == [record["id"]]


@pytest.mark.asyncio
async def test_recompute_bumps_schema_version_and_preserves_created_at():
    tenant_a = str(uuid.uuid4())
    store = PostgresGtmStore(capability="market_sizing")

    first = await store.compute(
        tenant_id=tenant_a, name="Recompute", industries=["retail"], snapshot_id="qa-recompute-1"
    )
    second = await store.compute(
        tenant_id=tenant_a, name="Recompute", industries=["retail"], snapshot_id="qa-recompute-1"
    )

    f, s = first.as_dict(), second.as_dict()
    assert s["schema_version"] == f["schema_version"] + 1
    assert s["created_at"] == f["created_at"]
    assert s["id"] == f["id"] == "qa-recompute-1"


@pytest.mark.asyncio
async def test_force_rls_hides_other_tenant_and_unpinned_rows_from_salesos_app():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    store = PostgresGtmStore(capability="enrichment")
    await store.enrich(tenant_id=tenant_a, company_name="Alpha Co")
    await store.enrich(tenant_id=tenant_b, company_name="Beta Co")

    async with async_session() as session:
        await _set_tenant(session, None)
        zero = (await session.execute(text("SELECT count(*) AS n FROM gtm_capability_results"))).first().n
        assert zero == 0

        await _set_tenant(session, tenant_a)
        a_only = (
            await session.execute(text("SELECT count(*) AS n FROM gtm_capability_results"))
        ).first().n
        assert a_only == 1

        await _set_tenant(session, tenant_b)
        b_only = (
            await session.execute(text("SELECT count(*) AS n FROM gtm_capability_results"))
        ).first().n
        assert b_only == 1
        await session.rollback()


@pytest.mark.asyncio
async def test_cross_tenant_same_id_reuse_is_blocked():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    store = PostgresGtmStore(capability="market_sizing")
    await store.compute(tenant_id=tenant_a, name="A", snapshot_id="qa-shared-id")
    with pytest.raises(PermissionError):
        await store.compute(tenant_id=tenant_b, name="B", snapshot_id="qa-shared-id")


@pytest.mark.asyncio
async def test_sequencing_definitions_and_enrollments_round_trip():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    seq = PostgresGtmStore(capability=DEFINITION_CAPABILITY)

    definition = await seq.create_definition(
        tenant_id=tenant_a,
        name="QA Follow-up",
        steps=[
            {
                "id": "step-1",
                "day_offset": 0,
                "channel": "email",
                "subject": "Intro",
                "body": "Hello",
            },
            {
                "id": "step-2",
                "day_offset": 1,
                "channel": "email",
                "subject": "Bump",
                "body": "Following up",
            },
        ],
    )
    definition_id = definition.as_dict()["id"]
    assert definition.as_dict()["channel"] == "email"

    with pytest.raises(SequencingError):
        await seq.create_definition(
            tenant_id=tenant_a,
            name="Dup",
            steps=[
                {
                    "id": "step-1",
                    "day_offset": 0,
                    "channel": "email",
                    "subject": "Intro",
                    "body": "Hello",
                },
                {
                    "id": "step-2",
                    "day_offset": 1,
                    "channel": "email",
                    "subject": "Bump",
                    "body": "Following up",
                },
            ],
            definition_id=definition_id,
        )

    enrollment = await seq.enroll(
        tenant_id=tenant_a,
        sequence_id=definition_id,
        contact_email="qa@example.co",
    )
    enrollment_id = enrollment.as_dict()["id"]
    assert enrollment.as_dict()["status"] == "active"

    advanced = await seq.advance(enrollment_id, tenant_id=tenant_a)
    # Two-step definition: first advance sends step-1, leaves step-2 due, so
    # the enrollment stays active (pause/resume/cancel below stay legal).
    assert advanced.as_dict()["status"] == "active"
    assert advanced.as_dict()["current_step_index"] == 1

    paused = await seq.pause(enrollment_id, tenant_id=tenant_a)
    assert paused.as_dict()["status"] == "paused"
    resumed = await seq.resume(enrollment_id, tenant_id=tenant_a)
    assert resumed.as_dict()["status"] == "active"
    cancelled = await seq.cancel(enrollment_id, tenant_id=tenant_a)
    assert cancelled.as_dict()["status"] == "cancelled"

    assert (await seq.get_definition(definition_id, tenant_id=tenant_a)) is not None
    assert (await seq.get_enrollment(enrollment_id, tenant_id=tenant_a)) is not None
    assert [d.as_dict()["id"] for d in await seq.list_definitions(tenant_id=tenant_a)] == [
        definition_id
    ]
    assert [e.as_dict()["id"] for e in await seq.list_enrollments(tenant_id=tenant_a)] == [
        enrollment_id
    ]

    assert await seq.get_definition(definition_id, tenant_id=tenant_b) is None
    assert await seq.get_enrollment(enrollment_id, tenant_id=tenant_b) is None
    assert await seq.list_enrollments(tenant_id=tenant_b) == []