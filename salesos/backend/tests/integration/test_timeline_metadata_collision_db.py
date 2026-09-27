"""PostgresTimelineRepository.append() used to splat event.metadata directly
into the top-level JSONB payload dict alongside the reserved "actor"/
"target"/"outcome"/"event_id" serialization keys:

    payload = {"actor": ..., "target": ..., "outcome": ..., "event_id": ...,
               **event.metadata}

Since TimelineRecorder.on_domain_event() passes the *raw* domain-event
"data" dict as metadata (metadata=data), and the wildcard event subscriber
in app/boot/startup.py routes EVERY domain event published anywhere in the
app through this exact path, any real domain event whose data payload
happens to contain a top-level key literally named "actor", "target",
"outcome", or "event_id" would silently overwrite the serialized
actor/target/outcome/event_id fields at write time. If the overwritten
value has the wrong shape (e.g. a plain string instead of a dict), the
NEXT read of that row crashes _row_to_event() -> _deserialize_actor()/
_deserialize_target() with an unhandled AttributeError ('str' object has
no attribute 'get'), which poisons the entire page since query() rebuilds
every row in one list comprehension with no per-row exception handling.

Fixed by nesting metadata under its own "metadata" key on write (removing
the collision entirely) and hardening _deserialize_actor/_deserialize_target
to check isinstance(..., dict) before use (defends legacy/corrupted rows
too). Read is backward compatible: a row lacking a nested "metadata" key
falls back to the old flat-extraction shape.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import apply_tenant_guc, async_session, engine
from domains.timeline.contracts.models import (
    ActivityOutcome,
    ActivityType,
    Actor,
    ActorType,
    Target,
    TimelineEvent,
)
from domains.timeline.contracts.repository import TimelineQuery
from domains.timeline.engine.postgres_repo import PostgresTimelineRepository
from domains.timeline.models import TimelineEventModel


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
async def test_metadata_key_named_actor_does_not_corrupt_or_crash():
    """A caller-supplied metadata field literally named "actor" (a realistic
    shape for a domain event about e.g. a CRM contact's own "actor" role)
    must not corrupt the serialized Actor or crash the next read."""
    tenant_id = str(uuid.uuid4())
    real_actor = Actor(id="user-42", type=ActorType.USER, name="Real Caller")
    event = TimelineEvent(
        event_id=str(uuid.uuid4()),
        actor=real_actor,
        activity=ActivityType.COMPANY_UPDATED,
        target=Target(id="company-1", type="company", label="Acme"),
        outcome=ActivityOutcome.SUCCESS,
        # A plausible real domain-event payload shape: a field literally
        # named "actor" that is NOT the reserved Actor-serialization dict.
        metadata={"actor": "some-unrelated-string-value", "note": "quarterly review"},
        tenant_id=tenant_id,
    )

    async with async_session() as session:
        await apply_tenant_guc(session, tenant_id)
        repo = PostgresTimelineRepository(session)
        await repo.append(event)
        await session.commit()

    async with async_session() as session:
        await apply_tenant_guc(session, tenant_id)
        repo = PostgresTimelineRepository(session)
        result = await repo.query(
            TimelineQuery(target_id="company-1", target_type="company", tenant_id=tenant_id)
        )

    assert result.total == 1
    read_back = result.events[0]
    # The REAL actor (from event.actor) must survive untouched.
    assert read_back.actor.id == "user-42"
    assert read_back.actor.name == "Real Caller"
    # The caller's metadata, including its "actor" key, must round-trip.
    assert read_back.metadata["actor"] == "some-unrelated-string-value"
    assert read_back.metadata["note"] == "quarterly review"


@pytest.mark.asyncio
async def test_legacy_flat_splatted_row_still_reads_back():
    """Rows written before this fix (metadata splatted at the top level of
    the JSONB payload, no nested "metadata" key) must remain readable."""
    tenant_id = str(uuid.uuid4())
    legacy_row = TimelineEventModel(
        entity_type="company",
        entity_id="company-legacy",
        event_type="company.updated",
        data={
            "actor": {"id": "legacy-user", "type": "user", "name": "Legacy Actor"},
            "target": {"id": "company-legacy", "type": "company", "label": "Legacy Co"},
            "outcome": "success",
            "event_id": "legacy-evt-1",
            # Flat-splatted legacy metadata field, no nested "metadata" key.
            "some_legacy_field": "still readable",
        },
        actor="legacy-user",
        tenant_id=tenant_id,
    )

    async with async_session() as session:
        await apply_tenant_guc(session, tenant_id)
        session.add(legacy_row)
        await session.commit()

    async with async_session() as session:
        await apply_tenant_guc(session, tenant_id)
        repo = PostgresTimelineRepository(session)
        result = await repo.query(
            TimelineQuery(target_id="company-legacy", target_type="company", tenant_id=tenant_id)
        )

    assert result.total == 1
    read_back = result.events[0]
    assert read_back.actor.id == "legacy-user"
    assert read_back.actor.name == "Legacy Actor"
    assert read_back.metadata["some_legacy_field"] == "still readable"
