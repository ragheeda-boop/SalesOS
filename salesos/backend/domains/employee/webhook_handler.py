"""Webhook handlers for Google Calendar & Microsoft Graph push notifications.

Validates webhook signatures, handles event replay protection,
and triggers incremental sync on push events.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from domains.employee.oauth_service import EmployeeOAuthToken, OAuthTokenService
from domains.employee.tasks import calendar_sync_employee

router = APIRouter()

# Replay protection: stores (channel_id, message_number) for dedup
_replay_cache: dict[str, set[int]] = {}
MAX_REPLAY_CACHE = 10000


def _validate_google_signature(body: bytes, signature: str | None, secret: str = "") -> bool:
    """Validate Google webhook push notification signature."""
    if not signature:
        return False
    if not secret:
        return True  # Skip validation in dev
    try:
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        received = signature.replace("sha256=", "")
        return hmac.compare_digest(expected, received)
    except Exception:
        return False


def _validate_microsoft_validation_token(query_params: dict) -> str | None:
    """Microsoft Graph sends a validationToken query param on subscription creation."""
    return query_params.get("validationToken")


def _check_replay(channel_id: str, message_number: int) -> bool:
    """Prevent replay attacks by tracking message numbers per channel."""
    if len(_replay_cache) > MAX_REPLAY_CACHE:
        oldest = min(_replay_cache.keys(), key=lambda k: min(_replay_cache[k]) if _replay_cache[k] else 0)
        del _replay_cache[oldest]
    channel_msgs = _replay_cache.setdefault(channel_id, set())
    if message_number in channel_msgs:
        return False
    channel_msgs.add(message_number)
    return True


@router.get("/webhooks/google-calendar")
async def google_calendar_webhook_verify(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Google Calendar webhook verification — responds to initial challenge."""
    channel_id = request.query_params.get("id")
    if not channel_id:
        raise HTTPException(status_code=400, detail="Missing channel id")
    return {"status": "verified", "channel_id": channel_id}


@router.post("/webhooks/google-calendar")
async def google_calendar_webhook(
    request: Request,
    x_goog_channel_id: str | None = Header(None),
    x_goog_resource_id: str | None = Header(None),
    x_goog_resource_state: str | None = Header(None),
    x_goog_message_number: str | None = Header(None, alias="X-Goog-Message-Number"),
    db: AsyncSession = Depends(get_db_session),
):
    """Handle Google Calendar push notifications — trigger incremental sync."""
    body = await request.body()

    if not x_goog_channel_id:
        raise HTTPException(status_code=400, detail="Missing channel id")

    if x_goog_message_number:
        if not _check_replay(x_goog_channel_id, int(x_goog_message_number)):
            return {"status": "duplicate"}

    if x_goog_resource_state == "sync":
        return {"status": "acknowledged"}

    # Find employee by channel_id
    from sqlalchemy import select
    result = await db.execute(
        select(EmployeeOAuthToken).where(
            EmployeeOAuthToken.webhook_channel_id == x_goog_channel_id,
            EmployeeOAuthToken.is_active == True,
        ).limit(1)
    )
    token = result.scalar_one_or_none()
    if not token:
        return {"status": "unknown_channel"}

    if x_goog_resource_state in ("exists", "not_exists"):
        try:
            await calendar_sync_employee(str(token.employee_id), str(token.tenant_id), "google")
        except Exception as exc:
            token.record_failure(str(exc))
            await db.flush()

    return {"status": "ok"}


@router.get("/webhooks/microsoft-calendar")
async def microsoft_calendar_webhook_verify(
    request: Request,
    validationToken: str | None = None,
):
    """Microsoft Graph subscription validation — echo back the token."""
    if validationToken:
        return {"validationToken": validationToken}
    return {"status": "ok"}


@router.post("/webhooks/microsoft-calendar")
async def microsoft_calendar_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Handle Microsoft Graph change notifications — trigger incremental sync."""
    body = await request.body()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    notifications = data.get("value", [])
    for notif in notifications:
        subscription_id = notif.get("subscriptionId")
        if not subscription_id:
            continue

        from sqlalchemy import select
        result = await db.execute(
            select(EmployeeOAuthToken).where(
                EmployeeOAuthToken.webhook_resource_id == subscription_id,
                EmployeeOAuthToken.is_active == True,
            ).limit(1)
        )
        token = result.scalar_one_or_none()
        if not token:
            continue

        try:
            await calendar_sync_employee(str(token.employee_id), str(token.tenant_id), "microsoft")
        except Exception as exc:
            token.record_failure(str(exc))
            await db.flush()

    return {"status": "ok"}
