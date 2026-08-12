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


async def _hub_gmail_sync_all() -> dict[str, Any]:
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


async def _hub_calendar_sync_all() -> dict[str, Any]:
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
