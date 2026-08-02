"""STORY-08-05 — SyncRun + CAP-028 scheduling unit suite."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.integration_hub.sync_schedule import (
    KIND_INTEGRATION_HUB_SYNC,
    MemSyncRun,
    MemSyncRunLog,
    SyncRunExecutor,
    schedule_connection_sync,
    tick_with_sync_logging,
)
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.service import WorkflowService
from tests.support.tenant_isolation import assert_cross_tenant_read_blocked


@pytest.mark.asyncio
async def test_cap028_interval_tick_logs_sync_run() -> None:
    """AC: sync runs on schedule via CAP-028 and logs to SyncRun."""
    repo = InMemoryWorkflowRepository()
    wf = WorkflowService(repo)
    tenant = "tenant-a"
    connection_id = str(uuid.uuid4())
    log = MemSyncRunLog()

    async def _pull(tid: str, cid: str, model: str) -> dict:
        assert tid == tenant
        assert cid == connection_id
        assert model == "res.partner"
        return {
            "records": [{"id": 1}, {"id": 2}],
            "cursor": {"write_date": "2026-08-02T00:00:00Z"},
        }

    executor = SyncRunExecutor(log, pull=_pull)
    job = await schedule_connection_sync(
        wf,
        tenant_id=tenant,
        connection_id=connection_id,
        model="res.partner",
        schedule="15m",
        job_type="interval",
    )
    assert job.config["kind"] == KIND_INTEGRATION_HUB_SYNC
    assert job.config["scheduled_job_id"] == job.id
    job.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await repo.update_job(job)

    executions = await tick_with_sync_logging(wf, executor)
    assert len(executions) == 1
    assert executions[0].status == "completed"
    runs = log.for_tenant(tenant)
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "succeeded"
    assert run.records_pulled == 2
    assert run.records_written == 2
    assert run.scheduled_job_id == job.id
    assert run.cursor_after["write_date"] == "2026-08-02T00:00:00Z"
    assert executions[0].result["sync_run_id"] == str(run.id)


@pytest.mark.asyncio
async def test_connection_unreachable_classified() -> None:
    repo = InMemoryWorkflowRepository()
    wf = WorkflowService(repo)
    tenant = "tenant-a"
    connection_id = str(uuid.uuid4())
    log = MemSyncRunLog()

    async def _pull(tid: str, cid: str, model: str) -> dict:
        raise ConnectionError("odoo sandbox unreachable")

    executor = SyncRunExecutor(log, pull=_pull)
    job = await schedule_connection_sync(
        wf,
        tenant_id=tenant,
        connection_id=connection_id,
        model="res.partner",
        schedule="1m",
    )
    job.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await repo.update_job(job)
    executions = await tick_with_sync_logging(wf, executor)
    assert executions[0].status == "completed"
    run = log.for_tenant(tenant)[0]
    assert run.status == "failed"
    assert run.failure_class == "connection_unreachable"


@pytest.mark.asyncio
async def test_cross_tenant_sync_run_read_blocked() -> None:
    log = MemSyncRunLog()

    class _Store:
        async def create(self, tenant_id: str) -> uuid.UUID:
            rid = uuid.uuid4()
            log.rows.append(
                MemSyncRun(
                    id=rid,
                    tenant_id=tenant_id,
                    connection_id=str(uuid.uuid4()),
                    model="x",
                    status="succeeded",
                )
            )
            return rid

        async def get(self, key: uuid.UUID, tenant_id: str) -> MemSyncRun | None:
            for r in log.rows:
                if r.id == key and r.tenant_id == tenant_id:
                    return r
            return None

    store = _Store()
    await assert_cross_tenant_read_blocked(
        create_as=store.create,
        read_as=store.get,
        tenant_a="tenant-a",
        tenant_b="tenant-b",
    )
