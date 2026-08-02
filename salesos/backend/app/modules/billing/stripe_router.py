"""STORY-05-02 — Stripe webhook (public) + Owner checkout fail-closed.

No invented secrets. Empty STRIPE_* → fail closed (503/400), never accept unsigned.
DEC-085 untouched. Not Production GO.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db_session
from app.modules.billing.stripe_signature import StripeSignatureError, verify_stripe_signature
from app.modules.billing.stripe_webhook_service import StripeWebhookService
from app.owner_auth import require_owner_role_dep

logger = logging.getLogger(__name__)

webhook_router = APIRouter(tags=["Billing - Stripe Webhooks"])
owner_router = APIRouter(
    tags=["Admin - Billing Stripe"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)

STRIPE_WEBHOOK_PATH = "/api/v1/billing/stripe/webhook"


class CheckoutSessionRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    success_url: HttpUrl
    cancel_url: HttpUrl
    price_id: str | None = Field(
        None,
        description="Stripe Price id (price_...); required when Stripe is configured",
    )
    mode: str = Field("subscription", pattern="^(subscription|payment)$")


def stripe_configured() -> bool:
    return bool((settings.stripe_secret_key or "").strip())


def stripe_webhook_configured() -> bool:
    return bool((settings.stripe_webhook_secret or "").strip())


@webhook_router.post("/billing/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> dict[str, Any]:
    """Idempotent Stripe webhook. Signature required when secret configured."""
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

    svc = StripeWebhookService(db)
    result = await svc.process_event(event)
    await db.commit()
    return result


@owner_router.post("/billing/stripe/checkout-session")
async def create_checkout_session(body: CheckoutSessionRequest) -> dict[str, Any]:
    """Create Stripe Checkout Session (test/live key from env only). Fail-closed if unset."""
    secret = (settings.stripe_secret_key or "").strip()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Stripe secret key not configured (STRIPE_SECRET_KEY)",
        )
    if not body.price_id:
        raise HTTPException(status_code=400, detail="price_id is required")

    form = {
        "mode": body.mode,
        "success_url": str(body.success_url),
        "cancel_url": str(body.cancel_url),
        "line_items[0][price]": body.price_id,
        "line_items[0][quantity]": "1",
        "client_reference_id": body.tenant_id,
        "metadata[tenant_id]": body.tenant_id,
        "subscription_data[metadata][tenant_id]": body.tenant_id,
    }
    # httpx form-urlencoded for Stripe REST (no SDK; no invented keys).
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            content=urlencode(form),
            headers={
                "Authorization": f"Bearer {secret}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    if resp.status_code >= 400:
        logger.warning("stripe checkout failed status=%s", resp.status_code)
        raise HTTPException(
            status_code=502,
            detail="Stripe Checkout Session create failed (see server logs)",
        )
    data = resp.json()
    return {
        "id": data.get("id"),
        "url": data.get("url"),
        "mode": data.get("mode"),
        "tenant_id": body.tenant_id,
    }
