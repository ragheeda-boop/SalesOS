"""STORY-09-06 — account.move → OBJ-021 CustomerInvoice sync.

Deliberately distinct from OBJ-303/323 ``PlatformBillingInvoice`` (Owner-plane
Stripe mirror). Odoo customer AR invoices only — never platform billing rows.
No invented secrets. Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.modules.integration_hub.anti_corruption import (
    AclValidationError,
    CanonicalRecord,
    OdooTranslator,
)
from app.modules.integration_hub.types import PullRecord

# Customer AR move types (Odoo account.move) — never entry/in_invoice.
CUSTOMER_MOVE_TYPES = frozenset({"out_invoice", "out_refund"})

# Canonical payment states for CustomerInvoice (DOM-006 Revenue Intelligence).
CANONICAL_PAYMENT_STATES = frozenset(
    {
        "not_paid",
        "in_payment",
        "paid",
        "partial",
        "reversed",
        "cancelled",
    }
)

DEFAULT_PAYMENT_STATE_MAP: dict[str, str] = {
    "not_paid": "not_paid",
    "in_payment": "in_payment",
    "paid": "paid",
    "partial": "partial",
    "reversed": "reversed",
    "cancel": "cancelled",
    "cancelled": "cancelled",
}

DEFAULT_INVOICE_MAPPINGS: list[dict[str, Any]] = [
    {"internal": "name", "external": "name", "direction": "pull"},
    {"internal": "amount_total", "external": "amount_total", "direction": "pull"},
    {"internal": "amount_residual", "external": "amount_residual", "direction": "pull"},
    {"internal": "payment_state", "external": "payment_state", "direction": "pull"},
    {"internal": "partner_external_id", "external": "partner_id", "direction": "pull"},
]

_OPTIONAL_INVOICE_EXTERNALS: tuple[tuple[str, str], ...] = (
    ("invoice_date", "invoice_date"),
    ("invoice_date_due", "invoice_date_due"),
    ("currency", "currency_id"),
    ("move_type", "move_type"),
    ("ref", "ref"),
)


@dataclass(frozen=True)
class CustomerInvoice:
    """OBJ-021 CustomerInvoice projection — not PlatformBillingInvoice."""

    external_id: str
    payload: dict[str, Any]
    partner_external_id: str | None = None

    @property
    def object_key(self) -> str:
        return "customer_invoice"


@dataclass
class CustomerInvoiceItem:
    external_id: str
    record: CanonicalRecord
    invoice: CustomerInvoice
    partner_external_id: str | None = None


@dataclass
class InvoiceSyncBatchResult:
    synced: list[CustomerInvoiceItem] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)

    @property
    def records_pulled(self) -> int:
        return len(self.synced) + len(self.failed) + len(self.skipped)


def _many2one_id(raw: Any) -> str | None:
    if raw is None or raw is False:
        return None
    if isinstance(raw, list | tuple) and raw:
        return str(raw[0]).strip() or None
    if isinstance(raw, Mapping) and "id" in raw:
        return str(raw["id"]).strip() or None
    text = str(raw).strip()
    return text or None


def _map_payment_state(raw: Any) -> str:
    key = str(raw or "").strip().lower()
    if not key:
        raise AclValidationError(
            "ACL rejected record: payment_state missing",
            field="payment_state",
        )
    mapped = DEFAULT_PAYMENT_STATE_MAP.get(key)
    if mapped is None:
        raise AclValidationError(
            f"ACL rejected record: payment_state {key!r} has no canonical "
            f"CustomerInvoice mapping (raw passthrough forbidden)",
            field="payment_state",
        )
    if mapped not in CANONICAL_PAYMENT_STATES:
        raise AclValidationError(
            f"ACL rejected record: payment_state {mapped!r} not canonical",
            field="payment_state",
        )
    return mapped


async def sync_customer_invoices(
    records: Sequence[PullRecord] | Sequence[Mapping[str, Any]],
    *,
    sync_run_id: str,
    mappings: list[Mapping[str, Any]] | None = None,
    translator: OdooTranslator | None = None,
) -> InvoiceSyncBatchResult:
    """Translate Odoo account.move customer invoices → CustomerInvoice."""
    acl = translator or OdooTranslator()
    maps = list(mappings or DEFAULT_INVOICE_MAPPINGS)
    out = InvoiceSyncBatchResult()

    for raw in records:
        if isinstance(raw, PullRecord):
            external_id = raw.external_id
            payload = dict(raw.payload)
            updated_at = raw.updated_at
        else:
            external_id = str(raw.get("id") or raw.get("external_id") or "")
            payload = dict(raw)
            updated_at = None

        move_type = str(payload.get("move_type") or "").strip()
        if move_type and move_type not in CUSTOMER_MOVE_TYPES:
            out.skipped.append(
                {
                    "external_id": external_id,
                    "kind": "not_customer_invoice",
                    "message": (
                        f"account.move move_type={move_type!r} skipped "
                        f"(CustomerInvoice is out_invoice/out_refund only; "
                        f"never PlatformBillingInvoice)"
                    ),
                }
            )
            continue

        try:
            active_maps = list(maps)
            if payload.get("partner_id") in (None, False, ""):
                active_maps = [
                    m
                    for m in active_maps
                    if not (isinstance(m, Mapping) and m.get("internal") == "partner_external_id")
                ]
            canonical = acl.translate(
                payload,
                mappings=active_maps,
                sync_run_id=sync_run_id,
                source_updated_at=updated_at,
            )
            # payment_state via dedicated map (not stage_map enums).
            pay_raw = canonical.payload.get("payment_state")
            if pay_raw is None:
                pay_raw = payload.get("payment_state")
            canonical.payload["payment_state"] = _map_payment_state(pay_raw)

            for internal, external in _OPTIONAL_INVOICE_EXTERNALS:
                if external in payload and payload.get(external) not in (None, False, ""):
                    canonical.payload[internal] = payload.get(external)

            partner_ext = _many2one_id(
                canonical.payload.get("partner_external_id") or payload.get("partner_id")
            )
            canonical.payload["partner_external_id"] = partner_ext
            canonical.payload["object_key"] = "customer_invoice"
            # Hard guard: never confuse with Owner-plane Stripe invoices.
            canonical.payload["not_platform_billing_invoice"] = True
            if "stripe_invoice_id" in canonical.payload:
                raise AclValidationError(
                    "CustomerInvoice must not carry stripe_invoice_id "
                    "(PlatformBillingInvoice field)",
                    field="stripe_invoice_id",
                )

            cur = canonical.payload.get("currency")
            if isinstance(cur, list | tuple) and len(cur) >= 2:
                canonical.payload["currency"] = str(cur[1]).strip()
            elif isinstance(cur, list | tuple) and cur:
                canonical.payload["currency"] = str(cur[0]).strip()

            invoice = CustomerInvoice(
                external_id=external_id or "unknown",
                payload=dict(canonical.payload),
                partner_external_id=partner_ext,
            )
            out.synced.append(
                CustomerInvoiceItem(
                    external_id=external_id or "unknown",
                    record=canonical,
                    invoice=invoice,
                    partner_external_id=partner_ext,
                )
            )
        except AclValidationError as exc:
            out.failed.append(
                {
                    "external_id": external_id,
                    "kind": "malformed_data",
                    "message": str(exc),
                    "field": exc.field,
                }
            )
        except Exception as exc:
            out.failed.append(
                {
                    "external_id": external_id,
                    "kind": "unknown",
                    "message": str(exc),
                }
            )
    return out
