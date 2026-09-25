"""PersistentDeadLetterQueue had no tenant GUC pinning anywhere, and
purge_old() used a bind parameter inside a quoted INTERVAL literal that
asyncpg cannot compile at all.

Mechanical findings, `runtime/event_runtime/persistent_dlq.py` — this class
IS live (wired into every `EventRuntime` in production via
`app/boot/startup.py`'s `EventRuntime(session_factory=async_session, ...)`,
and `add()` is called for real whenever a subscriber exhausts its retries),
unlike this session's prior dead-code findings:

1. **No GUC pinning anywhere**: `event_dead_letters` has RLS + FORCE RLS;
   none of `add`/`list_all`/`count`/`mark_replayed`/`purge_old` ever pinned
   `app.tenant_id`. Every real `add()` call — the one live path, invoked on
   subscriber exhaustion — silently failed its `WITH CHECK` and was caught
   by the method's own `except Exception: logger.error(...)`, meaning the
   persistent-storage guarantee this class exists for
   ("dead-lettered events survive process restarts") has never actually
   held; only the separate in-memory `DeadLetterQueue` was ever populated.
2. **`purge_old()`'s `INTERVAL ':days days'`**: a bind parameter embedded
   inside a quoted string literal is not a valid asyncpg positional
   parameter — confirmed in isolation
   (`asyncpg.exceptions._base.InterfaceError: the server expects 0
   arguments for this query, 1 was passed`). Every real call raised, was
   caught by this method's own except, and silently returned 0 — old,
   already-replayed dead-letter rows were never purged. Fixed to
   `make_interval(days => :days)`.

`list_all`/`count`/`mark_replayed`/`purge_old` have zero callers anywhere
in the codebase today (confirmed via repo-wide grep — the REST endpoints
at `runtime/event_runtime/router.py` read the separate in-memory
`dead_letter_queue`, not this class) — fixed ahead of any future caller,
same posture as reports 73/74's findings, but `add()` itself is genuinely
live today and was silently losing data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from runtime.event_runtime.persistent_dlq import PersistentDeadLetterQueue


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed_tenant(session, tenant_id: str) -> None:
    await session.execute(
        text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'DLQ Test', :slug)"),
        {"id": tenant_id, "slug": f"dlq-test-{tenant_id[:8]}"},
    )


@pytest.mark.asyncio
async def test_add_persists_under_rls_and_is_tenant_scoped():
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_a}
        )
        await _seed_tenant(session, tenant_a)
        await session.commit()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_b}
        )
        await _seed_tenant(session, tenant_b)
        await session.commit()

    dlq = PersistentDeadLetterQueue(async_session)
    await dlq.add(
        entry_id=str(uuid.uuid4()),
        tenant_id=tenant_a,
        event_id="evt-1",
        event_type="decision.created",
        subscriber_name="test_subscriber",
        error="boom",
        attempts=3,
    )

    # Must genuinely persist (the old bug silently discarded this).
    a_count = await dlq.count(tenant_a)
    assert a_count == 1

    # Fail-closed: tenant B must never see tenant A's dead-lettered event.
    b_count = await dlq.count(tenant_b)
    assert b_count == 0

    a_entries = await dlq.list_all(tenant_a)
    assert len(a_entries) == 1
    assert a_entries[0]["event_id"] == "evt-1"


@pytest.mark.asyncio
async def test_purge_old_deletes_replayed_entries_past_the_window():
    tenant_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await _seed_tenant(session, tenant_id)
        await session.commit()

    dlq = PersistentDeadLetterQueue(async_session)
    old_entry_id = str(uuid.uuid4())
    recent_entry_id = str(uuid.uuid4())
    old_failed_at = datetime.now(timezone.utc) - timedelta(days=60)
    await dlq.add(
        entry_id=old_entry_id,
        tenant_id=tenant_id,
        event_id="evt-old",
        event_type="decision.created",
        subscriber_name="test_subscriber",
        error="boom",
        attempts=3,
        failed_at=old_failed_at,
    )
    await dlq.add(
        entry_id=recent_entry_id,
        tenant_id=tenant_id,
        event_id="evt-recent",
        event_type="decision.created",
        subscriber_name="test_subscriber",
        error="boom",
        attempts=3,
    )
    await dlq.mark_replayed(old_entry_id, tenant_id)
    await dlq.mark_replayed(recent_entry_id, tenant_id)

    # Must not raise (the old ":days days" bind syntax always raised here,
    # caught, and returned 0) and must actually delete the old, replayed row.
    purged = await dlq.purge_old(tenant_id, older_than_days=30)
    assert purged == 1

    remaining = await dlq.list_all(tenant_id)
    assert len(remaining) == 1
    assert remaining[0]["event_id"] == "evt-recent"
