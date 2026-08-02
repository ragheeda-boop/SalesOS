"""STORY-08-05 — CAP-028 Scheduled Jobs bridge for Integration Hub sync.

Schedules incremental sync via existing workflow JobScheduler (CAP-028).
Each due tick logs a SyncRun. Does not invent secrets. Not Production GO.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from domains.workflow.models import ScheduledJob
from domains.workflow.scheduler import JobScheduler
from domains.workflow.service import WorkflowService

KIND_INTEGRATION_HUB_SYNC = "integration_hub_sync"

PullFn = Callable[[str, str, str], Awaitable[dict[str, Any]]]


@dataclass
class MemSyncRun:
    """In-memory SyncRun row for unit / CAP-028 tick tests."""

    id: uuid.UUID
    tenant_id: str
    connection_id: str
    model: str
    status: str
    scheduled_job_id: str | None = None
    failure_class: str | None = None
    cursor_before: dict[str, Any] = field(default_factory=dict)
    cursor_after: dict[str, Any] = field(default_factory=dict)
    records_pulled: int = 0
    records_written: int = 0
    records_failed: int = 0
    error_log: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class MemSyncRunLog:
    rows: list[MemSyncRun] = field(default_factory=list)

    def for_tenant(self, tenant_id: str) -> list[MemSyncRun]:
        return [r for r in self.rows if r.tenant_id == tenant_id]


class SyncRunExecutor:
    """Execute one scheduled sync and append a SyncRun log entry."""

    def __init__(self, log: MemSyncRunLog, *, pull: PullFn | None = None) -> None:
        self.log = log
        self._pull = pull

    async def run(
        self,
        config: Mapping[str, Any],
        payload: Mapping[str, Any],
        tenant_id: str,
    ) -> dict[str, Any]:
        connection_id = str(config.get("connection_id") or "").strip()
        model = str(config.get("model") or "").strip()
        if not connection_id or not model:
            raise ValueError("integration_hub_sync requires connection_id + model")
        started = datetime.now(UTC)
        run = MemSyncRun(
            id=uuid.uuid4(),
            tenant_id=str(tenant_id),
            connection_id=connection_id,
            model=model,
            status="running",
            scheduled_job_id=str(config.get("scheduled_job_id") or "") or None,
            cursor_before=dict(config.get("cursor") or {}),
            started_at=started,
        )
        self.log.rows.append(run)
        try:
            if self._pull is None:
                result = {
                    "records": list(payload.get("records") or []),
                    "cursor": dict(payload.get("cursor") or config.get("cursor") or {}),
                    "cursor_before": dict(config.get("cursor") or {}),
                }
            else:
                result = await self._pull(tenant_id, connection_id, model)
            # STORY-09-07: pull may supply cursor_before from persisted write_date.
            if result.get("cursor_before") is not None:
                run.cursor_before = dict(result.get("cursor_before") or {})
            records = list(result.get("records") or [])
            failed = list(result.get("failed") or [])
            run.records_pulled = len(records) + len(failed)
            run.records_written = len(records)
            run.records_failed = len(failed)
            run.cursor_after = dict(result.get("cursor") or {})
            if failed and records:
                run.status = "partial"
                run.failure_class = "malformed_data"
                run.error_log = [{"kind": "malformed_data", "count": len(failed)}]
            elif failed and not records:
                run.status = "failed"
                run.failure_class = str(result.get("failure_class") or "malformed_data")
                run.error_log = list(result.get("errors") or [{"kind": run.failure_class}])
            else:
                run.status = "succeeded"
            run.finished_at = datetime.now(UTC)
            return {
                "sync_run_id": str(run.id),
                "status": run.status,
                "records_pulled": run.records_pulled,
                "records_written": run.records_written,
                "records_failed": run.records_failed,
            }
        except ConnectionError as exc:
            run.status = "failed"
            run.failure_class = "connection_unreachable"
            run.error_log = [{"kind": "connection_unreachable", "message": str(exc)}]
            run.finished_at = datetime.now(UTC)
            return {
                "sync_run_id": str(run.id),
                "status": run.status,
                "failure_class": run.failure_class,
            }


async def schedule_connection_sync(
    workflow: WorkflowService,
    *,
    tenant_id: str,
    connection_id: str | uuid.UUID,
    model: str,
    schedule: str = "15m",
    job_type: str = "interval",
    name: str | None = None,
) -> ScheduledJob:
    """Register a CAP-028 job that triggers Integration Hub incremental sync."""
    cid = str(connection_id).strip()
    model_name = (model or "").strip()
    if not cid or not model_name:
        raise ValueError("connection_id and model are required")
    if job_type not in {"cron", "interval", "one_time"}:
        raise ValueError(f"invalid job_type: {job_type}")
    label = name or f"hub-sync:{cid[:8]}:{model_name}"
    job = await workflow.create_job(
        tenant_id=str(tenant_id),
        name=label,
        job_type=job_type,
        schedule=schedule,
        config={
            "kind": KIND_INTEGRATION_HUB_SYNC,
            "connection_id": cid,
            "model": model_name,
        },
        payload={},
    )
    # Stamp job id into config so SyncRun can reference CAP-028 source.
    job.config = {**dict(job.config or {}), "scheduled_job_id": job.id}
    return await workflow._repo.update_job(job)


def attach_sync_handlers(scheduler: JobScheduler, executor: SyncRunExecutor) -> None:
    """Wrap CAP-028 schedule-type handlers so hub sync jobs log SyncRun rows."""
    for jt in ("cron", "interval", "one_time"):
        prior = scheduler._handlers.get(jt)

        async def _handler(
            config: Mapping[str, Any],
            payload: Mapping[str, Any],
            tenant_id: str,
            *,
            _prior: Any = prior,
            _jt: str = jt,
        ) -> dict[str, Any]:
            if dict(config or {}).get("kind") == KIND_INTEGRATION_HUB_SYNC:
                return await executor.run(config, payload, tenant_id)
            if _prior is not None:
                result = await _prior(config, payload, tenant_id)
                return dict(result) if result is not None else {"ok": True}
            return {"skipped": True, "reason": f"no handler for {_jt}"}

        scheduler.register_handler(jt, _handler)


async def tick_with_sync_logging(
    workflow: WorkflowService,
    executor: SyncRunExecutor,
    *,
    now: datetime | None = None,
) -> list[Any]:
    """Run one CAP-028 scheduler tick with Integration Hub handlers attached."""
    scheduler = JobScheduler(workflow._repo)
    attach_sync_handlers(scheduler, executor)
    return await scheduler.tick(now=now)
