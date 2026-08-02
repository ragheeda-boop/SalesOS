"""Stripe webhook signature verification — pure HMAC (no Stripe SDK).

STORY-05-02. Fail-closed when secret is empty. Does not invent credentials.
See https://stripe.com/docs/webhooks/signatures
"""

from __future__ import annotations

import hashlib
import hmac
import time


class StripeSignatureError(ValueError):
    """Invalid or missing Stripe-Signature."""


def parse_stripe_signature_header(header: str) -> tuple[int, list[str]]:
    """Return (timestamp, list of v1 signatures)."""
    if not header or not header.strip():
        raise StripeSignatureError("missing Stripe-Signature header")
    ts: int | None = None
    v1s: list[str] = []
    for part in header.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        if key == "t":
            try:
                ts = int(val)
            except ValueError as exc:
                raise StripeSignatureError("invalid signature timestamp") from exc
        elif key == "v1" and val:
            v1s.append(val)
    if ts is None or not v1s:
        raise StripeSignatureError("Stripe-Signature missing t or v1")
    return ts, v1s


def verify_stripe_signature(
    *,
    payload: bytes,
    signature_header: str,
    webhook_secret: str,
    tolerance_seconds: int = 300,
    now: float | None = None,
) -> None:
    """Raise ``StripeSignatureError`` unless a v1 HMAC matches.

    Fail-closed: empty ``webhook_secret`` always raises (no unsigned accept).
    """
    secret = (webhook_secret or "").strip()
    if not secret:
        raise StripeSignatureError("stripe_webhook_secret not configured")

    ts, v1s = parse_stripe_signature_header(signature_header)
    clock = now if now is not None else time.time()
    if abs(int(clock) - ts) > int(tolerance_seconds):
        raise StripeSignatureError("signature timestamp outside tolerance")

    signed = f"{ts}.".encode("utf-8") + payload
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, sig) for sig in v1s):
        raise StripeSignatureError("signature mismatch")
