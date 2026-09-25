"""hub_gmail_sync_all()/hub_calendar_sync_all()'s per-account sync loop never
pinned the tenant GUC before constructing GmailSyncService/CalendarSyncService.

Mechanical finding, `app/modules/communication_hub/tasks.py` — these Celery
tasks are code-ready but not currently executed in production (no worker
service provisioned, per the module's own docstring); fixed ahead of that
wiring, same posture as this session's other dead/inactive-code findings.

`google_accounts` has RLS + FORCE RLS. Both `_hub_gmail_sync_all()` and
`_hub_calendar_sync_all()` open a fresh, unpinned session per account and
pass it straight to `GmailSyncService`/`CalendarSyncService`, whose `sync()`
immediately calls `GoogleAccountRepository.get_by_user()` — under RLS with
no GUC pinned, that query finds nothing regardless of how many real,
matching accounts exist, and `sync()` raises `GmailSyncError`/
`CalendarSyncError` ("No active Google account connected") on every call.
Fixed by pinning `apply_tenant_guc(db, str(account.tenant_id))` before
constructing the sync service for that account.

A second, separate, NOT-fixed-here finding is also documented: the earlier
`GoogleAccountRepository(db).list_active()` step — the cross-tenant
enumeration that discovers which accounts to sync in the first place — is
itself unpinned and returns 0 rows under the restricted `salesos_app` role
regardless of GUC state (RLS enforces a single-tenant view; there is no
"list across all tenants" carve-out on this connection). Fixing that
requires a deliberate RLS-bypass session (e.g. `owner_engine`), which is an
infra/architecture decision left open, not made unilaterally here — this
test therefore exercises the per-account fix directly via
`GoogleAccountRepository.get_by_user()` (the same first call `sync()`
makes), rather than through the full `list_active()` → per-account loop,
since the latter cannot discover any account today regardless of this fix.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import apply_tenant_guc, async_session, engine
from app.modules.communication_hub.repository import GoogleAccountRepository


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


async def _seed_account(tenant_id: str, user_id: str, account_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        await session.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, 'Hub Task Test', :slug)"),
            {"id": tenant_id, "slug": f"hub-task-{tenant_id[:8]}"},
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
async def test_get_by_user_finds_the_account_only_when_guc_is_pinned_for_its_tenant():
    """Reproduces the exact first call GmailSyncService/CalendarSyncService.sync()
    makes, mirroring what the tasks.py per-account loop now does."""
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    account_id = str(uuid.uuid4())
    await _seed_account(tenant_id, user_id, account_id)

    # Unpinned session: matches the pre-fix tasks.py behavior.
    async with async_session() as session:
        repo = GoogleAccountRepository(session)
        account = await repo.get_by_user(uuid.UUID(tenant_id), uuid.UUID(user_id))
        assert account is None

    # Pinned session: matches the fixed tasks.py behavior.
    async with async_session() as session:
        await apply_tenant_guc(session, tenant_id)
        repo = GoogleAccountRepository(session)
        account = await repo.get_by_user(uuid.UUID(tenant_id), uuid.UUID(user_id))
        assert account is not None
        assert str(account.id) == account_id


@pytest.mark.asyncio
async def test_cross_tenant_enumeration_finds_every_tenants_active_accounts():
    """PO decision B8 (report 99): enumerate tenants, pin each, list its
    accounts — least privilege, no RLS bypass. The old unpinned list_active()
    saw none of them."""
    from app.modules.communication_hub.tasks import _active_accounts_all_tenants

    seeded = []
    for _ in range(2):
        tid, uid, aid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        await _seed_account(tid, uid, aid)
        seeded.append(aid)

    async with async_session() as db:
        unpinned = {str(a.id) for a in await GoogleAccountRepository(db).list_active()}
    assert not unpinned & set(seeded)

    found = {str(a.id) for a in await _active_accounts_all_tenants()}
    assert set(seeded) <= found
