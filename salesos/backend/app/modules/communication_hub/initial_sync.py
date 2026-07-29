"""First-sync after Google OAuth connect — Gmail + Calendar (+ contact upsert).

Triggered from the OAuth callback so Emp360/Comm Hub populate without a
manual Sync click. Failures are logged; they never fail the OAuth redirect.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


async def run_initial_sync(tenant_id: UUID, user_id: UUID) -> dict:
    """Run Gmail then Calendar sync with a fresh DB session."""
    from app.database import async_session
    from app.modules.communication_hub.calendar_sync import (
        CalendarSyncError,
        CalendarSyncService,
    )
    from app.modules.communication_hub.gmail_sync import GmailSyncError, GmailSyncService

    results: dict = {"gmail": None, "calendar": None, "errors": []}

    async with async_session() as db:
        try:
            gmail = GmailSyncService(db, tenant_id, user_id)
            results["gmail"] = await gmail.sync(days_lookback=30, max_results=100)
        except (GmailSyncError, Exception) as e:
            logger.warning(
                "initial_sync.gmail.failed",
                extra={"tenant_id": str(tenant_id), "user_id": str(user_id), "error": str(e)},
            )
            results["errors"].append(f"gmail: {e}")
            await db.rollback()

    async with async_session() as db:
        try:
            cal = CalendarSyncService(db, tenant_id, user_id)
            results["calendar"] = await cal.sync(days_lookback=90, days_forward=90)
        except (CalendarSyncError, Exception) as e:
            logger.warning(
                "initial_sync.calendar.failed",
                extra={"tenant_id": str(tenant_id), "user_id": str(user_id), "error": str(e)},
            )
            results["errors"].append(f"calendar: {e}")
            await db.rollback()

    logger.info(
        "initial_sync.completed",
        extra={
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "gmail_synced": (results["gmail"] or {}).get("synced_count"),
            "calendar_synced": (results["calendar"] or {}).get("synced_count"),
            "error_count": len(results["errors"]),
        },
    )
    return results


def schedule_initial_sync(tenant_id: UUID, user_id: UUID) -> None:
    """Fire-and-forget first sync (does not block OAuth redirect)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("initial_sync.no_event_loop", extra={"tenant_id": str(tenant_id)})
        return

    task = loop.create_task(run_initial_sync(tenant_id, user_id))

    def _done(t: asyncio.Task) -> None:
        try:
            t.result()
        except Exception:
            logger.exception(
                "initial_sync.task_failed",
                extra={"tenant_id": str(tenant_id), "user_id": str(user_id)},
            )

    task.add_done_callback(_done)
