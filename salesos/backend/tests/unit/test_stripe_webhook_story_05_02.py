"""STORY-05-02 — Stripe signature + event map + fail-closed (no invented keys)."""

from __future__ import annotations

import hashlib
import hmac
import time

import pytest

from app.modules.billing.state_machine import SubscriptionEvent
from app.modules.billing.stripe_events import (
    extract_tenant_id_from_stripe_object,
    map_stripe_event_to_subscription_event,
)
from app.modules.billing.stripe_signature import (
    StripeSignatureError,
    verify_stripe_signature,
)


def _sign(payload: bytes, secret: str, ts: int | None = None) -> str:
    clock = ts if ts is not None else int(time.time())
    signed = f"{clock}.".encode() + payload
    dig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={clock},v1={dig}"


def test_verify_signature_ok() -> None:
    secret = "whsec_test_fixture_not_a_real_key"
    payload = b'{"id":"evt_1","type":"invoice.paid"}'
    header = _sign(payload, secret)
    verify_stripe_signature(payload=payload, signature_header=header, webhook_secret=secret)


def test_verify_fail_closed_empty_secret() -> None:
    with pytest.raises(StripeSignatureError, match="not configured"):
        verify_stripe_signature(
            payload=b"{}",
            signature_header=_sign(b"{}", "x"),
            webhook_secret="",
        )


def test_verify_mismatch_and_tolerance() -> None:
    secret = "whsec_test_fixture_not_a_real_key"
    payload = b"{}"
    with pytest.raises(StripeSignatureError, match="mismatch"):
        verify_stripe_signature(
            payload=payload,
            signature_header=_sign(payload, "other"),
            webhook_secret=secret,
        )
    old = _sign(payload, secret, ts=int(time.time()) - 10_000)
    with pytest.raises(StripeSignatureError, match="tolerance"):
        verify_stripe_signature(payload=payload, signature_header=old, webhook_secret=secret)


@pytest.mark.parametrize(
    ("etype", "status", "expected"),
    [
        ("invoice.paid", None, SubscriptionEvent.ACTIVATE),
        ("invoice.payment_failed", None, SubscriptionEvent.MARK_PAST_DUE),
        ("customer.subscription.deleted", None, SubscriptionEvent.CHURN),
        ("customer.subscription.updated", "past_due", SubscriptionEvent.MARK_PAST_DUE),
        ("customer.subscription.updated", "active", SubscriptionEvent.ACTIVATE),
        ("customer.subscription.updated", "unpaid", SubscriptionEvent.SUSPEND),
        ("customer.subscription.updated", "canceled", SubscriptionEvent.CHURN),
        ("ping", None, None),
    ],
)
def test_event_map(etype: str, status: str | None, expected: SubscriptionEvent | None) -> None:
    assert map_stripe_event_to_subscription_event(etype, stripe_status=status) == expected


def test_extract_tenant_metadata() -> None:
    assert (
        extract_tenant_id_from_stripe_object(
            {"metadata": {"tenant_id": "11111111-1111-1111-1111-111111111111"}}
        )
        == "11111111-1111-1111-1111-111111111111"
    )
    assert extract_tenant_id_from_stripe_object({}) is None


def test_csrf_public_path_includes_stripe_webhook() -> None:
    from app.common.middleware import CsrfEnforcementMiddleware

    assert "/api/v1/billing/stripe/webhook" in CsrfEnforcementMiddleware._PUBLIC_PATHS


def test_suspension_guard_skips_stripe_webhook() -> None:
    from app.modules.identity.tenant_lifecycle_guard import path_skips_suspension_guard

    assert path_skips_suspension_guard("/api/v1/billing/stripe/webhook") is True
