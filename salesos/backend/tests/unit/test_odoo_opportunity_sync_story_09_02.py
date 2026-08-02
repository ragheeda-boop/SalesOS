"""STORY-09-02 — Opportunity sync via crm.lead with translated stages."""

from __future__ import annotations

import pytest

from app.modules.integration_hub.anti_corruption import AclValidationError
from app.modules.integration_hub.odoo_adapter import InMemoryOdooRpc, OdooAdapter
from app.modules.integration_hub.opportunity_sync import (
    CANONICAL_OPPORTUNITY_STAGES,
    opportunity_translator,
    sync_opportunity_records,
)
from app.modules.integration_hub.types import WriteBackRequest


@pytest.mark.asyncio
async def test_opportunity_stages_translated_not_raw_passthrough() -> None:
    """AC: Odoo stage semantics translated, not passed through raw."""
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="crm.lead",
            external_id="501",
            payload={
                "name": "Acme expansion",
                "type": "opportunity",
                "stage_id": [2, "Qualified"],
                "expected_revenue": 15000.0,
                "partner_id": [10, "Acme SA"],
                "currency_id": [1, "SAR"],
                "description": "<p>Deal note</p>",
            },
        ),
    )
    # Lead (not opportunity) must not appear in crm.lead opportunity pull.
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="crm.lead",
            external_id="502",
            payload={
                "name": "Cold lead",
                "type": "lead",
                "stage_id": [1, "New"],
                "expected_revenue": 0,
                "partner_id": [10, "Acme SA"],
                "currency_id": [1, "SAR"],
            },
        ),
    )
    pulled = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="crm.lead",
        cursor=None,
        limit=50,
    )
    assert len(pulled.records) == 1
    assert pulled.records[0].external_id == "501"

    batch = await sync_opportunity_records(pulled.records, sync_run_id="sr-opp-1")
    assert batch.records_pulled == 1
    assert len(batch.synced) == 1
    assert len(batch.failed) == 0
    item = batch.synced[0]
    assert item.record.payload["stage"] == "qualification"
    assert item.record.payload["stage"] in CANONICAL_OPPORTUNITY_STAGES
    assert item.record.payload["stage"] != "2"
    assert item.record.payload["stage"] != "Qualified"
    assert item.partner_external_id == "10"
    assert item.record.payload["note"] == "Deal note"
    assert item.record.payload["amount_minor"] == 1_500_000


@pytest.mark.asyncio
async def test_unmapped_odoo_stage_rejected_loudly() -> None:
    """Raw / unknown Odoo stage must not land as passthrough."""
    batch = await sync_opportunity_records(
        [
            {
                "id": "99",
                "name": "Mystery deal",
                "type": "opportunity",
                "stage_id": [999, "Custom Weird Stage"],
                "expected_revenue": 100,
                "partner_id": [1, "X"],
                "currency_id": [1, "SAR"],
            }
        ],
        sync_run_id="sr-opp-2",
    )
    assert len(batch.synced) == 0
    assert len(batch.failed) == 1
    assert batch.failed[0]["field"] == "stage"
    assert "passthrough forbidden" in batch.failed[0]["message"]


def test_strict_translator_rejects_unmapped_stage() -> None:
    t = opportunity_translator()
    with pytest.raises(AclValidationError, match="passthrough forbidden"):
        t.translate(
            {
                "name": "x",
                "stage_id": "nope",
                "expected_revenue": 1,
                "partner_id": "1",
            },
            mappings=[
                {"internal": "name", "external": "name", "direction": "pull"},
                {"internal": "stage", "external": "stage_id", "direction": "pull"},
                {"internal": "amount", "external": "expected_revenue", "direction": "pull"},
                {
                    "internal": "partner_external_id",
                    "external": "partner_id",
                    "direction": "pull",
                },
            ],
            sync_run_id="sr-x",
        )


@pytest.mark.asyncio
async def test_won_lost_stage_aliases_translate() -> None:
    batch = await sync_opportunity_records(
        [
            {
                "id": "1",
                "name": "Won deal",
                "type": "opportunity",
                "stage_id": "won",
                "expected_revenue": 50,
                "partner_id": 7,
                "currency_id": "SAR",
            },
            {
                "id": "2",
                "name": "Lost deal",
                "type": "opportunity",
                "stage_id": "lost",
                "expected_revenue": 10,
                "partner_id": 7,
                "currency_id": "SAR",
            },
        ],
        sync_run_id="sr-opp-3",
    )
    assert len(batch.synced) == 2
    stages = {i.external_id: i.record.payload["stage"] for i in batch.synced}
    assert stages["1"] == "closed_won"
    assert stages["2"] == "closed_lost"
