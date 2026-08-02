"""STORY-09-01 residual — unlinked cr_number badge list API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.modules.integration_hub.cr_number_join import CrJoinResult
from app.modules.integration_hub.partner_sync import (
    company_lookup_from_index,
    sync_partner_records,
)
from app.modules.integration_hub.sync_schedule import (
    MemSyncRunLog,
    SyncRunExecutor,
    schedule_connection_sync,
    tick_with_sync_logging,
)
from app.modules.integration_hub.unlinked_badge import (
    KIND_UNLINKED_BADGE,
    MemUnlinkedBadgeStore,
    badge_dicts_for_error_log,
    badge_items_from_join_results,
    badge_items_from_partner_batch,
    collect_unlinked_badges_from_error_logs,
)
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.service import WorkflowService


@pytest.mark.asyncio
async def test_partner_batch_produces_unlinked_badge_items() -> None:
    index = {"1111111111": {"id": "co-1"}}
    batch = await sync_partner_records(
        [
            {
                "id": "10",
                "name": "Matched",
                "email": "a@ex.com",
                "phone": "0501111111",
                "x_studio_cr_number": "1111111111",
            },
            {
                "id": "11",
                "name": "Unlinked Co",
                "email": "b@ex.com",
                "phone": "0502222222",
                "x_studio_cr_number": "2222222222",
            },
            {
                "id": "12",
                "name": "Bad CR",
                "email": "c@ex.com",
                "phone": "0503333333",
                "x_studio_cr_number": "99",
            },
        ],
        sync_run_id="sr-badge-1",
        lookup_company=company_lookup_from_index(index),
    )
    assert len(batch.matched) == 1
    assert len(batch.unlinked) == 1
    assert len(batch.invalid) == 1
    items = badge_items_from_partner_batch(batch, sync_run_id="sr-badge-1")
    assert len(items) == 2
    statuses = {i.status for i in items}
    assert statuses == {"unlinked", "invalid_cr"}
    assert all(i.as_dict()["kind"] == KIND_UNLINKED_BADGE for i in items)

    store = MemUnlinkedBadgeStore()
    cid = str(uuid.uuid4())
    store.record(tenant_id="t-a", connection_id=cid, items=items)
    listed = store.list_for_connection(tenant_id="t-a", connection_id=cid)
    assert len(listed) == 2
    assert store.list_for_connection(tenant_id="t-b", connection_id=cid) == []


def test_collect_unlinked_badges_from_sync_run_error_logs() -> None:
    run = SimpleNamespace(
        id=uuid.uuid4(),
        model="res.partner",
        started_at=datetime.now(UTC),
        error_log=[
            {"kind": "malformed_data", "count": 1},
            {
                "kind": KIND_UNLINKED_BADGE,
                "status": "unlinked",
                "external_id": "99",
                "cr_number": "3333333333",
                "message": "no company/golden_record for cr_number — unlinked badge candidate",
                "model": "res.partner",
            },
        ],
    )
    items = collect_unlinked_badges_from_error_logs([run])
    assert len(items) == 1
    assert items[0].external_id == "99"
    assert items[0].status == "unlinked"
    assert items[0].cr_number == "3333333333"


@pytest.mark.asyncio
async def test_sync_run_executor_persists_unlinked_badges_in_error_log() -> None:
    """AC: scheduled sync surfaces unlinked badges on SyncRun (not silent)."""
    repo = InMemoryWorkflowRepository()
    wf = WorkflowService(repo)
    tenant = "tenant-badge"
    connection_id = str(uuid.uuid4())
    log = MemSyncRunLog()

    async def _pull(tid: str, cid: str, model: str) -> dict:
        assert tid == tenant
        assert cid == connection_id
        assert model == "res.partner"
        badges = badge_items_from_join_results(
            [
                CrJoinResult(
                    status="unlinked",
                    cr_number="4444444444",
                    external_id="77",
                    message="unlinked badge candidate",
                )
            ]
        )
        return {
            "records": [{"id": "1"}],
            "failed": [],
            "cursor": {"write_date": "2026-08-02T12:00:00Z"},
            "unlinked_badges": badge_dicts_for_error_log(badges),
        }

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
    await tick_with_sync_logging(wf, executor)
    run = log.for_tenant(tenant)[0]
    assert run.status == "succeeded"
    assert any(e.get("kind") == KIND_UNLINKED_BADGE for e in run.error_log)
    listed = collect_unlinked_badges_from_error_logs([run])
    assert len(listed) == 1
    assert listed[0].external_id == "77"
