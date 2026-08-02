"""STORY-09-01 — OdooAdapter + cr_number join to company dataset."""

from __future__ import annotations

import pytest

from app.modules.integration_hub.certify import certify_source_connector
from app.modules.integration_hub.cr_number_join import join_partner_by_cr_number
from app.modules.integration_hub.odoo_adapter import InMemoryOdooRpc, OdooAdapter
from app.modules.integration_hub.partner_sync import (
    company_lookup_from_index,
    sync_partner_records,
)
from app.modules.integration_hub.source_connector import SourceConnector
from app.modules.integration_hub.types import WriteBackRequest


def test_odoo_adapter_is_source_connector() -> None:
    assert isinstance(OdooAdapter(), SourceConnector)
    assert OdooAdapter().connector_key == "odoo"


@pytest.mark.asyncio
async def test_odoo_adapter_certifies_in_memory() -> None:
    result = await certify_source_connector(OdooAdapter())
    assert result["ok"] is True
    assert result["connector_key"] == "odoo"
    assert result["pulled"] >= 1


@pytest.mark.asyncio
async def test_cr_number_join_matches_company_dataset() -> None:
    """AC: cr_number join against company dataset (141k sim via index)."""
    dataset = {
        "1234567890": {"id": "co-1", "name": "Acme SA"},
        "0987654321": {"id": "co-2", "name": "Beta LLC"},
    }
    lookup = company_lookup_from_index(dataset)
    hit = await join_partner_by_cr_number(
        external_id="77",
        payload={"name": "Acme SA", "x_studio_cr_number": "1234567890"},
        lookup_company=lookup,
    )
    assert hit.status == "matched"
    assert hit.company_id == "co-1"
    assert hit.cr_number == "1234567890"

    miss = await join_partner_by_cr_number(
        external_id="88",
        payload={"name": "Unknown", "x_studio_cr_number": "1111111111"},
        lookup_company=lookup,
    )
    assert miss.status == "unlinked"
    assert "unlinked" in miss.message


@pytest.mark.asyncio
async def test_partner_sync_batch_matched_and_unlinked() -> None:
    dataset = {"1234567890": {"id": "co-1", "name": "Acme SA"}}
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="res.partner",
            external_id="1",
            payload={
                "name": "Acme SA",
                "email": "a@example.com",
                "phone": "0500000000",
                "x_studio_cr_number": "1234567890",
                "is_company": True,
            },
        ),
    )
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="res.partner",
            external_id="2",
            payload={
                "name": "Orphan Co",
                "email": "o@example.com",
                "phone": "0500000001",
                "x_studio_cr_number": "2222222222",
                "is_company": True,
            },
        ),
    )
    pulled = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="res.partner",
        cursor=None,
        limit=50,
    )
    batch = await sync_partner_records(
        pulled.records,
        sync_run_id="run-0901",
        lookup_company=company_lookup_from_index(dataset),
    )
    assert batch.records_pulled == 2
    assert len(batch.matched) == 1
    assert batch.matched[0].company_id == "co-1"
    assert len(batch.unlinked) == 1
    assert batch.unlinked[0].cr_number == "2222222222"


@pytest.mark.asyncio
async def test_incremental_cursor_advances() -> None:
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    for i, cr in enumerate(("1234567890", "1234567891"), start=1):
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
                    "x_studio_cr_number": cr,
                },
            ),
        )
    first = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="res.partner",
        cursor=None,
        limit=1,
    )
    assert len(first.records) == 1
    second = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="res.partner",
        cursor=first.next_cursor,
        limit=10,
    )
    assert all(r.external_id != first.records[0].external_id for r in second.records)
