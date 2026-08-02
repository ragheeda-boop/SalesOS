"""Idempotent Stripe webhook application → Subscription SM (STORY-05-02)."""

from __future__ import annotations

import uuid
from contextlib import suppress
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import StripeWebhookEventModel, SubscriptionModel
from app.modules.billing.service import SubscriptionService
from app.modules.billing.state_machine import (
    SubscriptionEvent,
    SubscriptionTransitionError,
    can_transition,
)
from app.modules.billing.stripe_events import (
    extract_tenant_id_from_stripe_object,
    map_stripe_event_to_subscription_event,
)


class StripeWebhookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subs = SubscriptionService(session)

    async def process_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Process one Stripe event dict. Idempotent on ``event.id``."""
        event_id = str(event.get("id") or "").strip()
        event_type = str(event.get("type") or "").strip()
        if not event_id or not event_type:
            return {"status": "rejected", "reason": "missing id or type"}

        existing = await self.session.get(StripeWebhookEventModel, event_id)
        if existing is not None:
            return {
                "status": "duplicate",
                "event_id": event_id,
                "event_type": event_type,
                "result": existing.result,
            }

        # Claim idempotency key first (unique PK) so concurrent deliveries coalesce.
        claim = StripeWebhookEventModel(
            event_id=event_id,
            event_type=event_type,
            tenant_id=None,
            result="processing",
        )
        try:
            async with self.session.begin_nested():
                self.session.add(claim)
                await self.session.flush()
        except IntegrityError:
            raced = await self.session.get(StripeWebhookEventModel, event_id)
            return {
                "status": "duplicate",
                "event_id": event_id,
                "event_type": event_type,
                "result": raced.result if raced else "race",
            }

        data_obj = (event.get("data") or {}).get("object") or {}
        if not isinstance(data_obj, dict):
            data_obj = {}

        tenant_id = extract_tenant_id_from_stripe_object(data_obj)
        stripe_status = data_obj.get("status") if isinstance(data_obj.get("status"), str) else None
        sm_event = map_stripe_event_to_subscription_event(event_type, stripe_status=stripe_status)

        result = "ignored"
        applied_to: str | None = None
        invoice_synced: str | None = None

        if event_type.startswith("invoice.") and isinstance(data_obj.get("id"), str):
            from app.modules.billing.stripe_invoice_sync import upsert_platform_invoice_from_stripe

            inv_row = await upsert_platform_invoice_from_stripe(self.session, data_obj)
            if inv_row is not None:
                invoice_synced = inv_row.stripe_invoice_id
                if tenant_id is None:
                    tenant_id = str(inv_row.tenant_id)
                if result == "ignored":
                    result = "invoice_synced"

        if sm_event is not None and tenant_id:
            applied = await self._apply_to_tenant(tenant_id, sm_event, data_obj)
            result = applied["result"]
            applied_to = applied.get("subscription_status")
        elif sm_event is not None and not tenant_id:
            applied = await self._apply_by_stripe_ids(sm_event, data_obj)
            result = applied["result"]
            applied_to = applied.get("subscription_status")
            tenant_id = applied.get("tenant_id")

        claim.result = result
        if tenant_id:
            with suppress(ValueError):
                claim.tenant_id = uuid.UUID(str(tenant_id))
        await self.session.flush()

        return {
            "status": "ok",
            "event_id": event_id,
            "event_type": event_type,
            "sm_event": sm_event.value if sm_event else None,
            "result": result,
            "subscription_status": applied_to,
            "tenant_id": tenant_id,
            "invoice_synced": invoice_synced,
        }

    async def _apply_to_tenant(
        self,
        tenant_id: str,
        sm_event: SubscriptionEvent,
        data_obj: dict[str, Any],
    ) -> dict[str, Any]:
        sub = await self.subs.get_by_tenant(tenant_id)
        if sub is None:
            sub, _ = await self.subs.ensure_for_tenant(tenant_id=tenant_id)
        self._stamp_stripe_ids(sub, data_obj)
        return await self._transition(sub, sm_event, data_obj=data_obj)

    async def _apply_by_stripe_ids(
        self,
        sm_event: SubscriptionEvent,
        data_obj: dict[str, Any],
    ) -> dict[str, Any]:
        stripe_sub = data_obj.get("subscription") or data_obj.get("id")
        customer = data_obj.get("customer")
        q = select(SubscriptionModel)
        if isinstance(stripe_sub, str) and stripe_sub.startswith("sub_"):
            q = q.where(SubscriptionModel.stripe_subscription_id == stripe_sub)
        elif isinstance(customer, str) and customer.startswith("cus_"):
            q = q.where(SubscriptionModel.stripe_customer_id == customer)
        else:
            return {"result": "no_tenant_metadata"}
        row = (await self.session.execute(q)).scalar_one_or_none()
        if row is None:
            return {"result": "subscription_not_found"}
        self._stamp_stripe_ids(row, data_obj)
        out = await self._transition(row, sm_event, data_obj=data_obj)
        out["tenant_id"] = str(row.tenant_id)
        return out

    def _stamp_stripe_ids(self, sub: SubscriptionModel, data_obj: dict[str, Any]) -> None:
        cust = data_obj.get("customer")
        if isinstance(cust, str) and cust.startswith("cus_"):
            sub.stripe_customer_id = cust
        sid = data_obj.get("subscription")
        if isinstance(sid, str) and sid.startswith("sub_"):
            sub.stripe_subscription_id = sid
        elif isinstance(data_obj.get("id"), str) and str(data_obj["id"]).startswith("sub_"):
            sub.stripe_subscription_id = str(data_obj["id"])

    async def _transition(
        self,
        sub: SubscriptionModel,
        sm_event: SubscriptionEvent,
        *,
        data_obj: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = sm_event
        payload = data_obj or {}
        if sm_event == SubscriptionEvent.ACTIVATE:
            if can_transition(sub.status, SubscriptionEvent.REACTIVATE):
                event = SubscriptionEvent.REACTIVATE
            elif can_transition(sub.status, SubscriptionEvent.RESUBSCRIBE_ACTIVE):
                event = SubscriptionEvent.RESUBSCRIBE_ACTIVE
            elif not can_transition(sub.status, SubscriptionEvent.ACTIVATE):
                return {"result": "noop", "subscription_status": sub.status}
        elif not can_transition(sub.status, event):
            return {"result": "noop", "subscription_status": sub.status}
        try:
            updated = await self.subs.apply_event(tenant_id=sub.tenant_id, event=event)
        except SubscriptionTransitionError:
            return {"result": "illegal", "subscription_status": sub.status}

        # STORY-05-04 — open/clear dunning around past_due / recovery.
        from app.modules.billing.dunning_service import DunningService

        dunning = DunningService(self.session)
        if event == SubscriptionEvent.MARK_PAST_DUE:
            inv_id = payload.get("id") if isinstance(payload.get("id"), str) else None
            if inv_id and not str(inv_id).startswith("in_"):
                inv_id = None
            await dunning.open_or_bump(tenant_id=sub.tenant_id, stripe_invoice_id=inv_id)
        elif event in {
            SubscriptionEvent.ACTIVATE,
            SubscriptionEvent.REACTIVATE,
            SubscriptionEvent.RESUBSCRIBE_ACTIVE,
        }:
            await dunning.clear_for_tenant(sub.tenant_id)

        return {"result": "applied", "subscription_status": updated.status}
