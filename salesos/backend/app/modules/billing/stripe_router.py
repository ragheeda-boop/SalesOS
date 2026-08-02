"""STORY-05-02 — Stripe webhook + Owner checkout/portal/catalog (fail-closed).

No invented secrets. Empty STRIPE_* → 503. DEC-085 untouched. Not Production GO.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db_session
from app.modules.admin.db_models import PlanModel
from app.modules.billing.models import PlatformBillingInvoiceModel
from app.modules.billing.service import SubscriptionService
from app.modules.billing.stripe_client import StripeNotConfiguredError, stripe_post_form
from app.modules.billing.stripe_signature import StripeSignatureError, verify_stripe_signature
from app.modules.billing.stripe_webhook_service import StripeWebhookService
from app.owner_auth import require_owner_role_dep

logger = logging.getLogger(__name__)

webhook_router = APIRouter(tags=["Billing - Stripe Webhooks"])
owner_router = APIRouter(
    tags=["Admin - Billing Stripe"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)


class CheckoutSessionRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    success_url: HttpUrl
    cancel_url: HttpUrl
    price_id: str | None = Field(
        None,
        description="Stripe Price id (price_...); or resolve via plan_id + billing_cycle",
    )
    plan_id: uuid.UUID | None = Field(None, description="admin_plans id for catalog lookup")
    billing_cycle: str = Field("monthly", pattern="^(monthly|yearly)$")
    mode: str = Field("subscription", pattern="^(subscription|payment)$")


class PortalSessionRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    return_url: HttpUrl


class PlanCatalogItem(BaseModel):
    id: uuid.UUID
    name: str
    tier: str
    price_monthly: float
    price_yearly: float
    stripe_price_id_monthly: str | None = None
    stripe_price_id_yearly: str | None = None
    is_active: bool


class PlatformInvoiceResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    stripe_invoice_id: str
    amount: float
    currency: str
    status: str
    description: str
    due_date: Any = None
    paid_at: Any = None
    hosted_invoice_url: str | None = None
    created_at: Any = None


def stripe_webhook_configured() -> bool:
    return bool((settings.stripe_webhook_secret or "").strip())


def stripe_secret_configured() -> bool:
    return bool((settings.stripe_secret_key or "").strip())


def stripe_publishable_configured() -> bool:
    return bool((settings.stripe_publishable_key or "").strip())


@owner_router.get("/billing/stripe/status")
async def stripe_config_status() -> dict[str, Any]:
    """STORY-05-02c — Owner readiness (booleans only; never echo secret values)."""
    secret_ok = stripe_secret_configured()
    webhook_ok = stripe_webhook_configured()
    publishable_ok = stripe_publishable_configured()
    return {
        "secret_key_configured": secret_ok,
        "webhook_secret_configured": webhook_ok,
        "publishable_key_configured": publishable_ok,
        "checkout_ready": secret_ok,
        "webhook_ready": webhook_ok,
        "sandbox_soak_ready": secret_ok and webhook_ok,
        "production_billing": False,
        "production_go": False,
        "honesty": "env-only secrets; empty STRIPE_* fail-closed 503",
    }


async def _resolve_price_id(db: AsyncSession, body: CheckoutSessionRequest) -> str:
    if body.price_id and body.price_id.strip():
        return body.price_id.strip()
    if body.plan_id is None:
        raise HTTPException(status_code=400, detail="price_id or plan_id is required")
    plan = await db.get(PlanModel, body.plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=404, detail="plan not found or inactive")
    price = (
        plan.stripe_price_id_yearly
        if body.billing_cycle == "yearly"
        else plan.stripe_price_id_monthly
    )
    if not price:
        raise HTTPException(
            status_code=400,
            detail=f"plan has no stripe_price_id_{body.billing_cycle} configured",
        )
    return str(price)


@webhook_router.post("/billing/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> dict[str, Any]:
    if not stripe_webhook_configured():
        raise HTTPException(
            status_code=503,
            detail="Stripe webhook secret not configured (STRIPE_WEBHOOK_SECRET)",
        )
    payload = await request.body()
    try:
        verify_stripe_signature(
            payload=payload,
            signature_header=stripe_signature or "",
            webhook_secret=settings.stripe_webhook_secret,
        )
    except StripeSignatureError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="invalid JSON payload") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="event must be object")
    result = await StripeWebhookService(db).process_event(event)
    await db.commit()
    return result


@owner_router.post("/billing/stripe/checkout-session")
async def create_checkout_session(
    body: CheckoutSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    price_id = await _resolve_price_id(db, body)
    form = {
        "mode": body.mode,
        "success_url": str(body.success_url),
        "cancel_url": str(body.cancel_url),
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "client_reference_id": body.tenant_id,
        "metadata[tenant_id]": body.tenant_id,
        "subscription_data[metadata][tenant_id]": body.tenant_id,
    }
    try:
        data = await stripe_post_form("/checkout/sessions", form)
    except StripeNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "id": data.get("id"),
        "url": data.get("url"),
        "mode": data.get("mode"),
        "tenant_id": body.tenant_id,
        "price_id": price_id,
    }


@owner_router.post("/billing/stripe/portal-session")
async def create_portal_session(
    body: PortalSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        tid = uuid.UUID(body.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid tenant_id") from exc
    sub = await SubscriptionService(db).get_by_tenant(tid)
    if sub is None or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=409,
            detail="tenant has no stripe_customer_id; complete Checkout first",
        )
    form = {"customer": sub.stripe_customer_id, "return_url": str(body.return_url)}
    try:
        data = await stripe_post_form("/billing_portal/sessions", form)
    except StripeNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "id": data.get("id"),
        "url": data.get("url"),
        "tenant_id": body.tenant_id,
        "stripe_customer_id": sub.stripe_customer_id,
    }


@owner_router.get("/billing/catalog", response_model=list[PlanCatalogItem])
async def list_billing_catalog(
    db: AsyncSession = Depends(get_db_session),
    active_only: bool = Query(True),
) -> list[PlanCatalogItem]:
    q = select(PlanModel)
    if active_only:
        q = q.where(PlanModel.is_active.is_(True))
    q = q.order_by(PlanModel.tier, PlanModel.name)
    rows = (await db.execute(q)).scalars().all()
    return [
        PlanCatalogItem(
            id=p.id,
            name=p.name,
            tier=p.tier,
            price_monthly=p.price_monthly,
            price_yearly=p.price_yearly,
            stripe_price_id_monthly=getattr(p, "stripe_price_id_monthly", None),
            stripe_price_id_yearly=getattr(p, "stripe_price_id_yearly", None),
            is_active=p.is_active,
        )
        for p in rows
    ]


@owner_router.get("/billing/platform-invoices", response_model=list[PlatformInvoiceResponse])
async def list_platform_invoices(
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str | None = Query(None),
) -> list[PlatformInvoiceResponse]:
    q = select(PlatformBillingInvoiceModel).order_by(PlatformBillingInvoiceModel.created_at.desc())
    if tenant_id:
        try:
            tid = uuid.UUID(tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid tenant_id") from exc
        q = q.where(PlatformBillingInvoiceModel.tenant_id == tid)
    rows = (await db.execute(q)).scalars().all()
    return [
        PlatformInvoiceResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            stripe_invoice_id=r.stripe_invoice_id,
            amount=r.amount,
            currency=r.currency,
            status=r.status,
            description=r.description,
            due_date=r.due_date,
            paid_at=r.paid_at,
            hosted_invoice_url=r.hosted_invoice_url,
            created_at=r.created_at,
        )
        for r in rows
    ]
