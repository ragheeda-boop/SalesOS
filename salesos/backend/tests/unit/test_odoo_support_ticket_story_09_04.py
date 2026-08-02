"""STORY-09-04 — SupportTicket sync via helpdesk.ticket."""

from __future__ import annotations

import pytest

from app.modules.integration_hub.odoo_adapter import InMemoryOdooRpc, OdooAdapter
from app.modules.integration_hub.ticket_sync import (
    CANONICAL_TICKET_STAGES,
    sync_support_tickets,
)
from app.modules.integration_hub.types import WriteBackRequest
from intelligence.guardrails import detect_pii_leakage


@pytest.mark.asyncio
async def test_helpdesk_ticket_synced_with_translated_stage() -> None:
    """AC: helpdesk.ticket synced correctly — stages translated, not raw."""
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="helpdesk.ticket",
            external_id="701",
            payload={
                "name": "Portal login issue",
                "stage_id": [2, "In Progress"],
                "priority": "1",
                "partner_id": [10, "Acme SA"],
                "user_id": [3, "Agent"],
                "description": "<p>Call Name: Nora at 0509876543</p>",
                "sla_deadline": "2026-08-10T12:00:00+00:00",
            },
        ),
    )
    pulled = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="helpdesk.ticket",
        cursor=None,
        limit=20,
    )
    assert len(pulled.records) == 1
    batch = await sync_support_tickets(pulled.records, sync_run_id="sr-tix-1")
    assert len(batch.synced) == 1
    assert len(batch.failed) == 0
    item = batch.synced[0]
    assert item.record.payload["stage"] == "in_progress"
    assert item.record.payload["stage"] in CANONICAL_TICKET_STAGES
    assert item.record.payload["stage"] != "2"
    assert item.partner_external_id == "10"
    assert item.record.payload["assignee_external_id"] == "3"
    assert detect_pii_leakage(str(item.record.payload.get("description") or "")) == []
    assert "0509876543" not in str(item.record.payload.get("description") or "")


@pytest.mark.asyncio
async def test_unmapped_ticket_stage_rejected() -> None:
    batch = await sync_support_tickets(
        [
            {
                "id": "99",
                "name": "Mystery",
                "stage_id": [999, "Weird"],
                "priority": "0",
                "partner_id": [1, "X"],
            }
        ],
        sync_run_id="sr-tix-2",
    )
    assert len(batch.synced) == 0
    assert len(batch.failed) == 1
    assert batch.failed[0]["field"] == "stage"
    assert "passthrough forbidden" in batch.failed[0]["message"]


@pytest.mark.asyncio
async def test_solved_cancelled_aliases() -> None:
    batch = await sync_support_tickets(
        [
            {
                "id": "1",
                "name": "Done",
                "stage_id": "done",
                "priority": "2",
                "partner_id": 7,
            },
            {
                "id": "2",
                "name": "Closed",
                "stage_id": "closed",
                "priority": "2",
                "partner_id": 7,
            },
        ],
        sync_run_id="sr-tix-3",
    )
    assert len(batch.synced) == 2
    stages = {i.external_id: i.record.payload["stage"] for i in batch.synced}
    assert stages["1"] == "solved"
    assert stages["2"] == "solved"
