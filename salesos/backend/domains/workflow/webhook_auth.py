"""Webhook authentication — HMAC signatures, JWT tokens, retry with backoff."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from domains.workflow.models import WebhookEndpoint

logger = logging.getLogger(__name__)

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None  # type: ignore[assignment]


def compute_hmac_signature(
    payload: bytes,
    secret: str,
    algorithm: str = "sha256",
) -> str:
    """Compute HMAC signature for webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload,
        getattr(hashlib, algorithm),
    ).hexdigest()


def verify_hmac_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256",
) -> bool:
    """Verify HMAC signature with constant-time comparison."""
    expected = compute_hmac_signature(payload, secret, algorithm)
    return hmac.compare_digest(expected, signature)


def generate_jwt_token(
    secret: str,
    payload: dict[str, Any],
    algorithm: str = "HS256",
    expires_in_seconds: int = 300,
) -> str:
    """Generate a JWT token for webhook authentication."""
    if pyjwt is None:
        raise ImportError("PyJWT is required for JWT webhook auth. Install with: pip install PyJWT")
    now = datetime.now(timezone.utc)
    claims = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + expires_in_seconds,
    }
    return pyjwt.encode(claims, secret, algorithm=algorithm)


def verify_jwt_token(
    token: str,
    secret: str,
    algorithm: str = "HS256",
) -> dict[str, Any]:
    """Verify and decode a JWT token."""
    if pyjwt is None:
        raise ImportError("PyJWT is required for JWT webhook auth. Install with: pip install PyJWT")
    return pyjwt.decode(token, secret, algorithms=[algorithm])


class WebhookAuthenticator:
    """Handles authentication for webhook delivery."""

    def __init__(self) -> None:
        self._max_retries = 3
        self._retry_delays = [0.5, 1.0, 2.0]  # exponential backoff in seconds

    def sign_request(
        self,
        endpoint: WebhookEndpoint,
        payload: dict[str, Any],
    ) -> dict[str, str]:
        """Sign a webhook request and return headers to attach."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        payload_bytes = json.dumps(payload, default=str).encode("utf-8")

        if endpoint.auth_type == "hmac":
            signature = compute_hmac_signature(payload_bytes, endpoint.secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"
            headers["X-Webhook-Signature-Algorithm"] = "sha256"
        elif endpoint.auth_type == "jwt":
            token = generate_jwt_token(
                secret=endpoint.secret,
                payload={"tenant_id": endpoint.tenant_id, "endpoint_id": endpoint.id},
            )
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def validate_incoming(
        self,
        endpoint: WebhookEndpoint,
        payload: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Validate an incoming webhook request's authentication."""
        if endpoint.auth_type == "none":
            return True

        if endpoint.auth_type == "hmac":
            sig_header = headers.get("X-Webhook-Signature", "")
            if not sig_header:
                logger.warning("Missing X-Webhook-Signature header for endpoint %s", endpoint.id)
                return False
            if sig_header.startswith("sha256="):
                sig_header = sig_header[7:]
            return verify_hmac_signature(payload, sig_header, endpoint.secret)

        if endpoint.auth_type == "jwt":
            auth_header = headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                logger.warning("Missing or invalid Authorization header for endpoint %s", endpoint.id)
                return False
            token = auth_header[7:]
            try:
                verify_jwt_token(token, endpoint.secret)
                return True
            except Exception as exc:
                logger.warning("JWT verification failed for endpoint %s: %s", endpoint.id, exc)
                return False

        return False

    def get_retry_delay(self, attempt: int) -> float:
        """Get retry delay for given attempt (0-indexed). Returns -1 if no more retries."""
        if attempt >= len(self._retry_delays):
            return -1
        return self._retry_delays[attempt]
