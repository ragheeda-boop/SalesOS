"""Tests for OAuth → first-sync scheduling and runner."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.communication_hub.initial_sync import run_initial_sync, schedule_initial_sync


@pytest.mark.asyncio
async def test_run_initial_sync_invokes_gmail_and_calendar():
    tenant_id = uuid4()
    user_id = uuid4()
    gmail_svc = AsyncMock()
    gmail_svc.sync = AsyncMock(
        return_value={"synced_count": 2, "new_count": 2, "updated_count": 0, "errors": []}
    )
    cal_svc = AsyncMock()
    cal_svc.sync = AsyncMock(
        return_value={
            "synced_count": 1,
            "new_count": 1,
            "updated_count": 0,
            "cancelled_count": 0,
            "errors": [],
        }
    )

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=AsyncMock())
    session_cm.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.database.async_session", return_value=session_cm),
        patch(
            "app.modules.communication_hub.gmail_sync.GmailSyncService",
            return_value=gmail_svc,
        ),
        patch(
            "app.modules.communication_hub.calendar_sync.CalendarSyncService",
            return_value=cal_svc,
        ),
    ):
        result = await run_initial_sync(tenant_id, user_id)

    assert result["gmail"]["synced_count"] == 2
    assert result["calendar"]["synced_count"] == 1
    assert result["errors"] == []
    gmail_svc.sync.assert_awaited_once()
    cal_svc.sync.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_initial_sync_records_partial_failure():
    tenant_id = uuid4()
    user_id = uuid4()
    gmail_svc = AsyncMock()
    gmail_svc.sync = AsyncMock(side_effect=Exception("no token"))
    cal_svc = AsyncMock()
    cal_svc.sync = AsyncMock(
        return_value={
            "synced_count": 0,
            "new_count": 0,
            "updated_count": 0,
            "cancelled_count": 0,
            "errors": [],
        }
    )

    db = AsyncMock()
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=db)
    session_cm.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.database.async_session", return_value=session_cm),
        patch(
            "app.modules.communication_hub.gmail_sync.GmailSyncService",
            return_value=gmail_svc,
        ),
        patch(
            "app.modules.communication_hub.calendar_sync.CalendarSyncService",
            return_value=cal_svc,
        ),
    ):
        result = await run_initial_sync(tenant_id, user_id)

    assert result["gmail"] is None
    assert any("gmail:" in e for e in result["errors"])
    assert result["calendar"] is not None


def test_schedule_initial_sync_creates_task():
    tenant_id = uuid4()
    user_id = uuid4()
    loop = MagicMock()
    task = MagicMock()
    loop.create_task.return_value = task

    with (
        patch("asyncio.get_running_loop", return_value=loop),
        patch(
            "app.modules.communication_hub.initial_sync.run_initial_sync",
            new=AsyncMock(),
        ),
    ):
        schedule_initial_sync(tenant_id, user_id)

    loop.create_task.assert_called_once()
    task.add_done_callback.assert_called_once()
