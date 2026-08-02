"""STORY-09-09 — SyncRun cursor_before/after on Hub HTTP (Monitor unblock)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.modules.integration_hub.schemas import SyncRunResponse


def test_sync_run_response_includes_cursor_before_after() -> None:
    """AC: SyncRunResponse exposes write_date cursors (not ORM-only)."""
    started = datetime.now(UTC)
    row = SimpleNamespace(
        id=uuid.uuid4(),
        connection_id=uuid.uuid4(),
        model="res.partner",
        status="succeeded",
        failure_class=None,
        records_pulled=2,
        records_written=2,
        records_failed=0,
        scheduled_job_id="job-1",
        cursor_before={"write_date": "2026-08-01T00:00:00Z"},
        cursor_after={"write_date": "2026-08-02T12:00:00Z"},
        started_at=started,
        finished_at=started,
    )
    resp = SyncRunResponse.model_validate(row)
    assert resp.cursor_before == {"write_date": "2026-08-01T00:00:00Z"}
    assert resp.cursor_after == {"write_date": "2026-08-02T12:00:00Z"}
    dumped = resp.model_dump()
    assert "cursor_before" in dumped
    assert "cursor_after" in dumped
    assert dumped["cursor_after"]["write_date"] == "2026-08-02T12:00:00Z"


def test_sync_run_response_defaults_empty_cursors() -> None:
    started = datetime.now(UTC)
    row = SimpleNamespace(
        id=uuid.uuid4(),
        connection_id=uuid.uuid4(),
        model="crm.lead",
        status="running",
        failure_class=None,
        records_pulled=0,
        records_written=0,
        records_failed=0,
        scheduled_job_id=None,
        cursor_before={},
        cursor_after={},
        started_at=started,
        finished_at=None,
    )
    resp = SyncRunResponse.model_validate(row)
    assert resp.cursor_before == {}
    assert resp.cursor_after == {}
