"""Celery tasks for Communication Hub Google sync (all active accounts).

Scheduled alongside Emp360 employee OAuth sync. Requires a Celery worker+beat
process — on Railway web-only deploys these tasks are code-ready but not
executed until a worker service is added (honest degraded).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any, cast

from celery import shared_task

logger = logging.getLogger(__name__)


def _run(coro: Coroutine[Any, Any, dict[str, Any]]) -> dict[str, Any]:
    """Bridge sync Celery tasks to async via a fresh event loop.

    Dispose module-level AsyncEngine on the same loop before asyncio.run
    returns so the next Celery tick does not hit loop-affinity errors.
    """

    async def _with_dispose() -> dict[str, Any]:
        try:
            return await coro
        finally:
            from app.database import engine

            try:
                await engine.dispose()
            except Exception:
                logger.warning(
                    "communication_hub tasks engine.dispose failed",
                    exc_info=True,
                )

    return cast(dict[str, Any], asyncio.run(_with_dispose()))


@shared_task(name="hub_gmail_sync_all", bind=True, max_retries=3, default_retry_delay=300)
def hub_gmail_sync_all(self) -> dict[str, Any]:
    return _run(_hub_gmail_sync_all())


@shared_task(name="hub_calendar_sync_all", bind=True, max_retries=3, default_retry_delay=300)
def hub_calendar_sync_all(self) -> dict[str, Any]:
    return _run(_hub_calendar_sync_all())


async def _active_accounts_all_tenants() -> list:
    """Active Google accounts across tenants without bypassing RLS.

    google_accounts is FORCE-RLS, so an unpinned listing sees nothing (report
    84). PO decision B8 (report 99) requires least privilege: rather than a
    BYPASSRLS/owner session — or a SECURITY DEFINER function, which under
    FORCE RLS would need an RLS-bypassing owner to see anything — enumerate
    tenants (not RLS-scoped) and list each tenant's accounts under its own pin.
    """
    from sqlalchemy import text

    from app.database import apply_tenant_guc, async_session
    from app.modules.communication_hub.repository import GoogleAccountRepository

    async with async_session() as db:
        tenant_ids = [str(r[0]) for r in (await db.execute(text("SELECT id FROM tenants"))).all()]
    accounts: list = []
    for tid in tenant_ids:
        async with async_session() as db:
            await apply_tenant_guc(db, tid)
            accounts.extend(await GoogleAccountRepository(db).list_active())
    return accounts


async def _hub_gmail_sync_all() -> dict[str, Any]:
    from app.database import apply_tenant_guc, async_session
    from app.modules.communication_hub.gmail_sync import GmailSyncError, GmailSyncService

    synced = 0
    failed = 0
    for account in await _active_accounts_all_tenants():
        try:
            async with async_session() as db:
                await apply_tenant_guc(db, str(account.tenant_id))
                svc = GmailSyncService(db, account.tenant_id, account.user_id)
                await svc.sync(days_lookback=7, max_results=100)
            synced += 1
        except (GmailSyncError, Exception) as e:
            failed += 1
            logger.warning(
                "hub_gmail_sync_all.failed",
                extra={"account_id": str(account.id), "error": str(e)},
            )
    return {"synced": synced, "failed": failed, "total": synced + failed}


async def _hub_calendar_sync_all() -> dict[str, Any]:
    from app.database import apply_tenant_guc, async_session
    from app.modules.communication_hub.calendar_sync import (
        CalendarSyncError,
        CalendarSyncService,
    )

    synced = 0
    failed = 0
    for account in await _active_accounts_all_tenants():
        try:
            async with async_session() as db:
                await apply_tenant_guc(db, str(account.tenant_id))
                svc = CalendarSyncService(db, account.tenant_id, account.user_id)
                await svc.sync(days_lookback=30, days_forward=30)
            synced += 1
        except (CalendarSyncError, Exception) as e:
            failed += 1
            logger.warning(
                "hub_calendar_sync_all.failed",
                extra={"account_id": str(account.id), "error": str(e)},
            )
    return {"synced": synced, "failed": failed, "total": synced + failed}
