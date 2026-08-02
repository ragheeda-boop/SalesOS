"""Map Stripe event types → SubscriptionEvent (STORY-05-02).

Pure mapping — no I/O. Sandbox/production mode is ops config, not code here.
"""

from __future__ import annotations

from app.modules.billing.state_machine import SubscriptionEvent

# Primary Stripe → SM edges (R-05 matrix substrate).
_EVENT_MAP: dict[str, SubscriptionEvent] = {
    "checkout.session.completed": SubscriptionEvent.ACTIVATE,
    "customer.subscription.created": SubscriptionEvent.ACTIVATE,
    "invoice.paid": SubscriptionEvent.ACTIVATE,
    "invoice.payment_succeeded": SubscriptionEvent.ACTIVATE,
    "invoice.payment_failed": SubscriptionEvent.MARK_PAST_DUE,
    "customer.subscription.deleted": SubscriptionEvent.CHURN,
}


def map_stripe_event_to_subscription_event(
    event_type: str,
    *,
    stripe_status: str | None = None,
) -> SubscriptionEvent | None:
    """Return SM event or None if ignored.

    ``customer.subscription.updated`` uses ``stripe_status`` when provided.
    """
    et = (event_type or "").strip()
    if et in _EVENT_MAP:
        return _EVENT_MAP[et]
    if et == "customer.subscription.updated":
        status = (stripe_status or "").strip().lower()
        if status in {"active", "trialing"}:
            return SubscriptionEvent.ACTIVATE
        if status == "past_due":
            return SubscriptionEvent.MARK_PAST_DUE
        if status in {"unpaid", "paused"}:
            return SubscriptionEvent.SUSPEND
        if status in {"canceled", "cancelled"}:
            return SubscriptionEvent.CHURN
    return None


def extract_tenant_id_from_stripe_object(obj: dict) -> str | None:
    """Read tenant_id from Checkout/Subscription metadata (Owner provision wire)."""
    if not isinstance(obj, dict):
        return None
    meta = obj.get("metadata") or {}
    if isinstance(meta, dict):
        tid = meta.get("tenant_id") or meta.get("salesos_tenant_id")
        if tid:
            return str(tid)
    # nested under data.object already expected by caller
    return None
