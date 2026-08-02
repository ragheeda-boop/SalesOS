"""STORY-09-05 — TaskCaseExtension VO on Task + project.task sync."""

from __future__ import annotations

import pytest

from app.modules.integration_hub.odoo_adapter import InMemoryOdooRpc, OdooAdapter
from app.modules.integration_hub.task_case_extension import (
    TaskCaseExtension,
    TaskCaseExtensionValidationError,
    build_task_case_extension,
)
from app.modules.integration_hub.task_sync import sync_project_tasks
from app.modules.integration_hub.types import WriteBackRequest


def test_task_case_extension_is_vo_not_aggregate() -> None:
    vo = TaskCaseExtension(
        case_type="financing",
        payload={
            "financing_amount_requested": 100000.0,
            "approved_financing_amount": 80000.0,
            "unified_agreement_status": "draft",
        },
    )
    data = vo.to_dict()
    assert "id" not in data
    assert data["case_type"] == "financing"


def test_json_schema_rejects_invalid_financing_payload() -> None:
    with pytest.raises(TaskCaseExtensionValidationError, match="financing"):
        TaskCaseExtension(
            case_type="financing",
            payload={"financing_amount_requested": -1},
        )


def test_classify_financing_vs_insurance_vs_none() -> None:
    fin = build_task_case_extension({"x_studio_financing_amount_requested": 50_000})
    assert fin is not None and fin.case_type == "financing"
    ins = build_task_case_extension(
        {
            "x_studio_coverage_value": 1_000_000,
            "x_studio_policy_provider": "Tawuniya",
        }
    )
    assert ins is not None and ins.case_type == "insurance"
    assert build_task_case_extension({"name": "Internal chore"}) is None


@pytest.mark.asyncio
async def test_project_task_sync_attaches_case_extension_vo() -> None:
    """AC: VO on Task, not standalone aggregate; schema-validated."""
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="project.task",
            external_id="801",
            payload={
                "name": "Acme financing underwriting",
                "stage_id": [2, "In Progress"],
                "x_studio_financing_amount_requested": 250000,
                "x_studio_approved_financing_amount": 200000,
                "x_studio_unified_agreement_status": "pending",
            },
        ),
    )
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="project.task",
            external_id="802",
            payload={
                "name": "SALES SUPPORT chore",
                "stage_id": [1, "New"],
            },
        ),
    )
    pulled = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="project.task",
        cursor=None,
        limit=20,
    )
    assert len(pulled.records) == 2
    batch = await sync_project_tasks(pulled.records, sync_run_id="sr-task-1")
    assert len(batch.synced) == 2
    by_id = {i.external_id: i for i in batch.synced}
    assert by_id["801"].case_extension is not None
    assert by_id["801"].case_extension.case_type == "financing"
    assert "id" not in by_id["801"].case_extension.to_dict()
    assert by_id["801"].record.payload["case_extension"]["case_type"] == "financing"
    assert by_id["802"].case_extension is None
    assert "case_extension" not in by_id["802"].record.payload
