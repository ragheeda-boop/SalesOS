"""STORY-09-06 — CustomerInvoice sync via account.move (≠ PlatformBillingInvoice)."""

from __future__ import annotations

import pytest

from app.modules.billing.models import PlatformBillingInvoiceModel
from app.modules.integration_hub.customer_invoice_sync import (
    CANONICAL_PAYMENT_STATES,
    CustomerInvoice,
    sync_customer_invoices,
)
from app.modules.integration_hub.odoo_adapter import InMemoryOdooRpc, OdooAdapter
from app.modules.integration_hub.types import WriteBackRequest


@pytest.mark.asyncio
async def test_account_move_customer_invoice_synced() -> None:
    """AC: account.move out_invoice → CustomerInvoice with payment_state mapped."""
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="account.move",
            external_id="9001",
            payload={
                "name": "INV/2026/0001",
                "move_type": "out_invoice",
                "amount_total": 12500.0,
                "amount_residual": 2500.0,
                "payment_state": "partial",
                "partner_id": [42, "Acme SA"],
                "invoice_date": "2026-07-01",
                "invoice_date_due": "2026-07-31",
                "currency_id": [1, "SAR"],
                "ref": "PO-778",
            },
        ),
    )
    # Vendor bill must not appear in customer AR pull.
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="account.move",
            external_id="9002",
            payload={
                "name": "BILL/2026/0001",
                "move_type": "in_invoice",
                "amount_total": 99.0,
                "amount_residual": 99.0,
                "payment_state": "not_paid",
                "partner_id": [7, "Vendor"],
            },
        ),
    )
    pulled = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="account.move",
        cursor=None,
        limit=20,
    )
    assert len(pulled.records) == 1
    assert pulled.records[0].external_id == "9001"

    batch = await sync_customer_invoices(pulled.records, sync_run_id="sr-inv-1")
    assert len(batch.synced) == 1
    assert len(batch.failed) == 0
    item = batch.synced[0]
    assert isinstance(item.invoice, CustomerInvoice)
    assert item.invoice.object_key == "customer_invoice"
    assert item.record.payload["payment_state"] == "partial"
    assert item.record.payload["payment_state"] in CANONICAL_PAYMENT_STATES
    assert item.record.payload["amount_total"] == 12500.0
    assert item.record.payload["amount_residual"] == 2500.0
    assert item.partner_external_id == "42"
    assert item.record.payload["invoice_date_due"] == "2026-07-31"
    assert item.record.payload["currency"] == "SAR"
    assert item.record.payload["not_platform_billing_invoice"] is True
    assert "stripe_invoice_id" not in item.record.payload


@pytest.mark.asyncio
async def test_non_customer_move_skipped() -> None:
    batch = await sync_customer_invoices(
        [
            {
                "id": "1",
                "name": "MISC",
                "move_type": "entry",
                "amount_total": 0,
                "amount_residual": 0,
                "payment_state": "paid",
            }
        ],
        sync_run_id="sr-inv-2",
    )
    assert len(batch.synced) == 0
    assert len(batch.skipped) == 1
    assert batch.skipped[0]["kind"] == "not_customer_invoice"


@pytest.mark.asyncio
async def test_unmapped_payment_state_rejected() -> None:
    batch = await sync_customer_invoices(
        [
            {
                "id": "2",
                "name": "INV/X",
                "move_type": "out_invoice",
                "amount_total": 10,
                "amount_residual": 10,
                "payment_state": "weird_odoo_state",
                "partner_id": [1, "X"],
            }
        ],
        sync_run_id="sr-inv-3",
    )
    assert len(batch.synced) == 0
    assert len(batch.failed) == 1
    assert batch.failed[0]["field"] == "payment_state"
    assert "passthrough forbidden" in batch.failed[0]["message"]


def test_customer_invoice_not_platform_billing_invoice() -> None:
    """AC: naming collision guard — CustomerInvoice ≠ PlatformBillingInvoice."""
    assert CustomerInvoice.__name__ != PlatformBillingInvoiceModel.__name__
    assert CustomerInvoice.__module__.endswith("customer_invoice_sync")
    assert PlatformBillingInvoiceModel.__tablename__ == "platform_billing_invoices"
    assert not hasattr(CustomerInvoice, "stripe_invoice_id")
    assert "stripe" not in CustomerInvoice.__module__
    inv = CustomerInvoice(external_id="1", payload={"object_key": "customer_invoice"})
    assert inv.object_key == "customer_invoice"
    assert inv.object_key != "platform_billing_invoice"
