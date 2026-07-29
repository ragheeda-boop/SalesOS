"""Celery tasks for Communication Hub Google sync (all active accounts).

Scheduled alongside Emp360 employee OAuth sync. Requires a Celery worker+beat
process — on Railway web-only deploys these tasks are code-ready but not
executed until a worker service is added (honest degraded).
"""

from __future__ import annotations

import asyncio
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


def _run(coro):
    """Bridge sync Celery tasks to async services via a fresh event loop."""
    return asyncio.run(coro)


@shared_task(name="hub_gmail_sync_all", bind=True, max_retries=3, default_retry_delay=300)
def hub_gmail_sync_all(self) -> dict:
    return _run(_hub_gmail_sync_all())


@shared_task(name="hub_calendar_sync_all", bind=True, max_retries=3, default_retry_delay=300)
def hub_calendar_sync_all(self) -> dict:
    return _run(_hub_calendar_sync_all())


async def _hub_gmail_sync_all() -> dict:
    from app.database import async_session
    from app.modules.communication_hub.gmail_sync import GmailSyncError, GmailSyncService
    from app.modules.communication_hub.repository import GoogleAccountRepository

    synced = 0
    failed = 0
    async with async_session() as db:
        accounts = await GoogleAccountRepository(db).list_active()
    for account in accounts:
        try:
            async with async_session() as db:
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


async def _hub_calendar_sync_all() -> dict:
    from app.database import async_session
    from app.modules.communication_hub.calendar_sync import (
        CalendarSyncError,
        CalendarSyncService,
    )
    from app.modules.communication_hub.repository import GoogleAccountRepository

    synced = 0
    failed = 0
    async with async_session() as db:
        accounts = await GoogleAccountRepository(db).list_active()
    for account in accounts:
        try:
            async with async_session() as db:
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
