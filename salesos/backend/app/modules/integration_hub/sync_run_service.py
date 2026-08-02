"""STORY-08-05 — SyncRun service (tenant-scoped observability).

Logs each scheduled pull to sync_runs. App-layer always filters by tenant_id.
Does not touch DEC-085. Not Production GO.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integration_hub.models import SyncRunModel

SyncStatus = Literal["pending", "running", "succeeded", "partial", "failed"]
FailureClass = Literal[
    "connection_unreachable",
    "field_mapping_drift",
    "malformed_data",
    "unknown",
]

_VALID_STATUS = frozenset({"pending", "running", "succeeded", "partial", "failed"})
_VALID_FAILURE = frozenset(
    {
        "connection_unreachable",
        "field_mapping_drift",
        "malformed_data",
        "unknown",
    }
)


class SyncRunService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start(
        self,
        *,
        tenant_id: uuid.UUID | str,
        connection_id: uuid.UUID | str,
        model: str,
        scheduled_job_id: str | None = None,
        cursor_before: Mapping[str, Any] | None = None,
        started_at: datetime | None = None,
    ) -> SyncRunModel:
        tid = uuid.UUID(str(tenant_id))
        cid = uuid.UUID(str(connection_id))
        model_name = (model or "").strip()
        if not model_name or len(model_name) > 128:
            raise ValueError("model required (max 128)")
        at = started_at or datetime.now(UTC)
        if at.tzinfo is None:
            at = at.replace(tzinfo=UTC)
        row = SyncRunModel(
            id=uuid.uuid4(),
            tenant_id=tid,
            connection_id=cid,
            scheduled_job_id=(scheduled_job_id or None),
            model=model_name,
            status="running",
            cursor_before=dict(cursor_before or {}),
            cursor_after={},
            records_pulled=0,
            records_written=0,
            records_failed=0,
            error_log=[],
            started_at=at,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def finish(
        self,
        run: SyncRunModel,
        *,
        tenant_id: uuid.UUID | str,
        status: SyncStatus,
        cursor_after: Mapping[str, Any] | None = None,
        records_pulled: int = 0,
        records_written: int = 0,
        records_failed: int = 0,
        error_log: Sequence[Mapping[str, Any]] | None = None,
        failure_class: FailureClass | None = None,
        finished_at: datetime | None = None,
    ) -> SyncRunModel:
        tid = uuid.UUID(str(tenant_id))
        if run.tenant_id != tid:
            raise PermissionError("cross-tenant SyncRun finish blocked")
        if status not in _VALID_STATUS:
            raise ValueError(f"invalid status: {status}")
        if failure_class is not None and failure_class not in _VALID_FAILURE:
            raise ValueError(f"invalid failure_class: {failure_class}")
        at = finished_at or datetime.now(UTC)
        if at.tzinfo is None:
            at = at.replace(tzinfo=UTC)
        run.status = status
        run.failure_class = failure_class
        run.cursor_after = dict(cursor_after or {})
        run.records_pulled = int(records_pulled)
        run.records_written = int(records_written)
        run.records_failed = int(records_failed)
        run.error_log = [dict(e) for e in (error_log or ())]
        run.finished_at = at
        await self.session.flush()
        return run

    async def get_for_tenant(
        self,
        run_id: uuid.UUID | str,
        *,
        tenant_id: uuid.UUID | str,
    ) -> SyncRunModel | None:
        rid = uuid.UUID(str(run_id))
        tid = uuid.UUID(str(tenant_id))
        q = await self.session.execute(
            select(SyncRunModel).where(
                SyncRunModel.id == rid,
                SyncRunModel.tenant_id == tid,
            )
        )
        return q.scalar_one_or_none()
