"""Upsert Stripe Invoice → platform_billing_invoices (OBJ-323 / STORY-05-02).

Pure mapping helpers + async upsert. No secrets. Not Production GO.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import PlatformBillingInvoiceModel, SubscriptionModel
from app.modules.billing.stripe_events import extract_tenant_id_from_stripe_object


def stripe_amount_to_major(amount: Any, currency: str) -> float:
    """Stripe amounts are in smallest currency unit (e.g. cents)."""
    try:
        minor = int(amount or 0)
    except (TypeError, ValueError):
        minor = 0
    # Zero-decimal currencies are rare for us; SAR/USD/EUR use 2 decimals.
    _ = currency
    return minor / 100.0


def map_stripe_invoice_status(status: str | None) -> str:
    s = (status or "open").strip().lower()
    if s in {"paid", "open", "draft", "uncollectible", "void"}:
        return s
    if s == "payment_failed":
        return "open"
    return s or "open"


def parse_unix_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


async def resolve_tenant_id_for_invoice(
    session: AsyncSession, invoice: dict[str, Any]
) -> uuid.UUID | None:
    tid = extract_tenant_id_from_stripe_object(invoice)
    if tid:
        try:
            return uuid.UUID(str(tid))
        except ValueError:
            pass
    customer = invoice.get("customer")
    if isinstance(customer, str) and customer.startswith("cus_"):
        row = (
            await session.execute(
                select(SubscriptionModel).where(SubscriptionModel.stripe_customer_id == customer)
            )
        ).scalar_one_or_none()
        if row is not None:
            return row.tenant_id
    return None


async def upsert_platform_invoice_from_stripe(
    session: AsyncSession, invoice: dict[str, Any]
) -> PlatformBillingInvoiceModel | None:
    """Idempotent upsert by stripe_invoice_id. Returns None if tenant unknown."""
    stripe_id = invoice.get("id")
    if not isinstance(stripe_id, str) or not stripe_id.startswith("in_"):
        return None
    tenant_id = await resolve_tenant_id_for_invoice(session, invoice)
    if tenant_id is None:
        return None

    existing = (
        await session.execute(
            select(PlatformBillingInvoiceModel).where(
                PlatformBillingInvoiceModel.stripe_invoice_id == stripe_id
            )
        )
    ).scalar_one_or_none()

    currency = str(invoice.get("currency") or "sar").upper()
    amount = stripe_amount_to_major(invoice.get("amount_due"), currency)
    if (
        invoice.get("amount_paid") is not None
        and map_stripe_invoice_status(invoice.get("status")) == "paid"
    ):
        amount = stripe_amount_to_major(invoice.get("amount_paid"), currency)
    status = map_stripe_invoice_status(
        invoice.get("status") if isinstance(invoice.get("status"), str) else None
    )
    description = ""
    lines = (
        (invoice.get("lines") or {}).get("data") if isinstance(invoice.get("lines"), dict) else None
    )
    if isinstance(lines, list) and lines:
        first = lines[0] if isinstance(lines[0], dict) else {}
        description = str(first.get("description") or "")[:2000]
    due = parse_unix_ts(invoice.get("due_date"))
    paid_at = (
        parse_unix_ts(invoice.get("status_transitions", {}).get("paid_at"))
        if isinstance(invoice.get("status_transitions"), dict)
        else None
    )
    if status == "paid" and paid_at is None:
        paid_at = parse_unix_ts(invoice.get("created"))

    if existing is None:
        row = PlatformBillingInvoiceModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            stripe_invoice_id=stripe_id,
            amount=amount,
            currency=currency[:10],
            status=status,
            description=description,
            due_date=due,
            paid_at=paid_at,
            hosted_invoice_url=(
                str(invoice["hosted_invoice_url"])
                if isinstance(invoice.get("hosted_invoice_url"), str)
                else None
            ),
        )
        session.add(row)
        await session.flush()
        return row

    existing.amount = amount
    existing.currency = currency[:10]
    existing.status = status
    existing.description = description or existing.description
    existing.due_date = due or existing.due_date
    existing.paid_at = paid_at or existing.paid_at
    if isinstance(invoice.get("hosted_invoice_url"), str):
        existing.hosted_invoice_url = invoice["hosted_invoice_url"]
    await session.flush()
    return existing
