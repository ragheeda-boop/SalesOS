"""run_initial_sync() (app/modules/communication_hub/initial_sync.py) never
pinned the tenant GUC before constructing GmailSyncService/CalendarSyncService
-- the exact same bug class report 84 fixed in the sibling file
app/modules/communication_hub/tasks.py, but in a separate, genuinely LIVE
call path that report 84 did not cover.

`google_accounts` has RLS + FORCE RLS. `GmailSyncService.sync()`/
`CalendarSyncService.sync()`'s first call is `self.repo.get_by_user(...)` --
under RLS with no GUC pinned, that call finds nothing regardless of how many
real, matching accounts exist, and `sync()` raises `GmailSyncError`/
`CalendarSyncError` ("No active Google account connected") on every call.

Reachability: `run_initial_sync()` is fired by `schedule_initial_sync()`,
called directly from `app/modules/communication_hub/router.py`'s real,
mounted Google OAuth callback route -- confirmed via grep, this is the
actual live route Google redirects to after a user completes OAuth connect.
Every real user who has ever connected Google through this flow would have
their promised "Emp360/Comm Hub populate without a manual Sync click"
(this module's own docstring) silently fail with "No active Google account
connected" -- on the very same account the same request just connected.

Fixed by pinning `apply_tenant_guc(db, str(tenant_id))` immediately after
opening each of the two fresh sessions, before constructing the sync
service -- matching tasks.py's established pattern exactly.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session, engine
from app.modules.communication_hub.calendar_sync import CalendarSyncService
from app.modules.communication_hub.gmail_sync import GmailSyncService
from app.modules.communication_hub.initial_sync import run_initial_sync


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


async def _seed_account(tenant_id: str, user_id: str, account_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Initial Sync Test', :slug)"),
            {"id": tenant_id, "slug": f"initsync-{tenant_id[:8]}"},
        )
        await session.execute(
            text("""
                INSERT INTO users (id, tenant_id, email, password_hash, full_name)
                VALUES (:id, :tid, :email, 'x', 'Test User')
            """),
            {"id": user_id, "tid": tenant_id, "email": f"user-{user_id[:8]}@example.com"},
        )
        await session.execute(
            text("""
                INSERT INTO google_accounts
                    (id, tenant_id, user_id, email, provider, access_token_encrypted, is_active)
                VALUES (:id, :tid, :uid, 'account@example.com', 'google', 'enc-token', true)
            """),
            {"id": account_id, "tid": tenant_id, "uid": user_id},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_run_initial_sync_reaches_the_provider_stage_for_a_real_seeded_account():
    """A discriminating proof: if the GUC pin is missing, execution never
    gets past the account lookup and both errors read "No active Google
    account connected". With the pin, it reaches the (mocked) provider
    stage instead, proving get_by_user() found the real account."""
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    account_id = str(uuid.uuid4())
    await _seed_account(tenant_id, user_id, account_id)

    with (
        patch.object(
            GmailSyncService, "_ensure_provider",
            side_effect=RuntimeError("test-marker: gmail reached provider stage"),
        ),
        patch.object(
            CalendarSyncService, "_ensure_provider",
            side_effect=RuntimeError("test-marker: calendar reached provider stage"),
        ),
    ):
        result = await run_initial_sync(uuid.UUID(tenant_id), uuid.UUID(user_id))

    assert any("test-marker: gmail reached provider stage" in e for e in result["errors"]), (
        result["errors"]
    )
    assert any("test-marker: calendar reached provider stage" in e for e in result["errors"]), (
        result["errors"]
    )
    assert not any("No active Google account connected" in e for e in result["errors"]), (
        result["errors"]
    )
