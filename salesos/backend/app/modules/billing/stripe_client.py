"""Minimal Stripe REST helper (httpx). Env secrets only — fail-closed.

STORY-05-02 follow-on. No SDK. No invented keys. Not Production GO.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

STRIPE_API = "https://api.stripe.com/v1"


class StripeNotConfiguredError(RuntimeError):
    """Raised when STRIPE_SECRET_KEY is empty."""


def require_stripe_secret() -> str:
    secret = (settings.stripe_secret_key or "").strip()
    if not secret:
        raise StripeNotConfiguredError("Stripe secret key not configured (STRIPE_SECRET_KEY)")
    return secret


async def stripe_post_form(path: str, form: dict[str, str]) -> dict[str, Any]:
    """POST application/x-www-form-urlencoded to Stripe. Raises on HTTP ≥400."""
    secret = require_stripe_secret()
    url = f"{STRIPE_API}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            content=urlencode(form),
            headers={
                "Authorization": f"Bearer {secret}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    if resp.status_code >= 400:
        logger.warning("stripe POST %s failed status=%s", path, resp.status_code)
        raise RuntimeError(f"Stripe API error status={resp.status_code}")
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError("Stripe API returned non-object JSON")
    return data
