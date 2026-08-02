"""STORY-09-07 — write_date cursor persistence + feature_odoo_integration."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.admin.repositories import InMemoryFeatureFlagRepository
from app.modules.integration_hub.odoo_adapter import InMemoryOdooRpc, OdooAdapter
from app.modules.integration_hub.odoo_incremental_sync import (
    FLAG_ODOO_INTEGRATION,
    MUHIDE_TENANT_SLUG,
    MemConnectionCursorStore,
    OdooIntegrationDisabledError,
    assert_odoo_integration_enabled,
    evaluate_feature_odoo_integration,
    pull_odoo_incremental_for_sync,
)
from app.modules.integration_hub.sync_schedule import (
    MemSyncRunLog,
    SyncRunExecutor,
    schedule_connection_sync,
    tick_with_sync_logging,
)
from app.modules.integration_hub.types import WriteBackRequest
from domains.workflow.repository import InMemoryWorkflowRepository
from domains.workflow.service import WorkflowService

# Fixture tenant standing in for Muhide design partner (not a prod secret).
MUHIDE_FIXTURE_TENANT_ID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


@pytest.mark.asyncio
async def test_feature_odoo_integration_seeded_globally_off() -> None:
    repo = InMemoryFeatureFlagRepository()
    flag = await repo.get_by_key(FLAG_ODOO_INTEGRATION)
    assert flag is not None
    assert flag.enabled is False
    eval_off = await repo.evaluate(FLAG_ODOO_INTEGRATION, MUHIDE_FIXTURE_TENANT_ID)
    assert eval_off["enabled"] is False
    assert eval_off["reason"] == "globally_disabled"


@pytest.mark.asyncio
async def test_muhide_tenant_override_enables_odoo_flag() -> None:
    """AC: feature_odoo_integration live for Muhide via tenant override."""
    repo = InMemoryFeatureFlagRepository()
    flag = await repo.get_by_key(FLAG_ODOO_INTEGRATION)
    assert flag is not None
    await repo.set_tenant_override(flag.id, MUHIDE_FIXTURE_TENANT_ID, True)
    # Other tenants remain off.
    other = await repo.evaluate(FLAG_ODOO_INTEGRATION, "other-tenant")
    assert other["enabled"] is False
    muhide = await repo.evaluate(FLAG_ODOO_INTEGRATION, MUHIDE_FIXTURE_TENANT_ID)
    assert muhide["enabled"] is True
    assert muhide["reason"] == "tenant_override"
    assert MUHIDE_TENANT_SLUG == "muhide"


def test_evaluate_helper_matches_grade_a_precedence() -> None:
    off = evaluate_feature_odoo_integration(flag_found=True, enabled=False, tenant_id="t1")
    assert off == {"enabled": False, "reason": "globally_disabled"}
    on = evaluate_feature_odoo_integration(
        flag_found=True,
        enabled=False,
        tenant_overrides={"t1": True},
        tenant_id="t1",
    )
    assert on == {"enabled": True, "reason": "tenant_override"}
    with pytest.raises(OdooIntegrationDisabledError):
        assert_odoo_integration_enabled(off)


@pytest.mark.asyncio
async def test_write_date_cursor_persists_across_scheduled_ticks() -> None:
    """AC: write_date cursor working end-to-end across two CAP-028 ticks."""
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    for i in range(1, 4):
        await adapter.write_back(
            credential_ref="vault://t/odoo",
            config={},
            request=WriteBackRequest(
                model="res.partner",
                external_id=str(i),
                payload={
                    "name": f"Co {i}",
                    "email": f"c{i}@ex.com",
                    "phone": "0500000000",
                    "x_studio_cr_number": f"123456789{i}",
                },
            ),
        )

    store = MemConnectionCursorStore()
    connection_id = str(uuid.uuid4())
    tenant = MUHIDE_FIXTURE_TENANT_ID
    flag_eval = evaluate_feature_odoo_integration(
        flag_found=True,
        enabled=False,
        tenant_overrides={tenant: True},
        tenant_id=tenant,
    )

    repo = InMemoryWorkflowRepository()
    wf = WorkflowService(repo)
    log = MemSyncRunLog()

    async def _pull(tid: str, cid: str, model: str) -> dict:
        return await pull_odoo_incremental_for_sync(
            adapter=adapter,
            credential_ref="vault://t/odoo",
            config={},
            model=model,
            connection_id=cid,
            tenant_id=tid,
            flag_eval=flag_eval,
            cursor_store=store,
            limit=1,
        )

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

    run1 = log.for_tenant(tenant)[0]
    assert run1.status == "succeeded"
    assert run1.records_pulled == 1
    assert run1.cursor_before == {}
    assert "write_date" in run1.cursor_after
    wm1 = run1.cursor_after["write_date"]
    assert store.get_watermark(connection_id, "res.partner") == wm1

    # Second tick must advance past first watermark.
    job.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await repo.update_job(job)
    await tick_with_sync_logging(wf, executor)
    run2 = log.for_tenant(tenant)[1]
    assert run2.status == "succeeded"
    assert run2.records_pulled == 1
    assert run2.cursor_before["write_date"] == wm1
    assert run2.cursor_after["write_date"] != wm1
    assert run2.cursor_after["write_date"] == store.get_watermark(connection_id, "res.partner")


@pytest.mark.asyncio
async def test_incremental_pull_blocked_when_flag_off() -> None:
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    store = MemConnectionCursorStore()
    with pytest.raises(OdooIntegrationDisabledError):
        await pull_odoo_incremental_for_sync(
            adapter=adapter,
            credential_ref="vault://t/odoo",
            config={},
            model="res.partner",
            connection_id=str(uuid.uuid4()),
            tenant_id="other",
            flag_eval={"enabled": False, "reason": "globally_disabled"},
            cursor_store=store,
        )
