"""Google Workspace integration router — Communication Hub.

Endpoints:
  GET  /api/v1/integrations/google/connect         — Start OAuth flow
  GET  /api/v1/integrations/google/callback         — OAuth callback (no auth required)
  GET  /api/v1/integrations/google/status           — Connection status
  POST /api/v1/integrations/google/disconnect       — Disconnect account
  POST /api/v1/integrations/google/sync             — Sync Gmail emails
  POST /api/v1/integrations/google/calendar-sync    — Sync Google Calendar
"""

import logging
from datetime import UTC
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_db_session,
    verify_token,
)
from app.modules.communication_hub.schemas import (
    GoogleAccountResponse,
    GoogleCalendarSyncRequest,
    GoogleCalendarSyncResponse,
    GoogleConnectResponse,
    GoogleDisconnectResponse,
    GoogleStatusResponse,
    GoogleSyncRequest,
    GoogleSyncResponse,
)
from app.modules.communication_hub.service import (
    GoogleOAuthError,
    GoogleOAuthService,
    google_oauth_config_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/google", tags=["Google Workspace"])

_AUTH = [Depends(verify_token)]


def _frontend_integrations_url(**params: str) -> str:
    base = (getattr(settings, "frontend_url", None) or "http://localhost:3000").rstrip("/")
    query = urlencode({k: v for k, v in params.items() if v is not None})
    path = f"{base}/v3/settings"
    return f"{path}?{query}" if query else path


def _get_service(
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
) -> GoogleOAuthService:
    return GoogleOAuthService(
        db, __import__("uuid").UUID(tenant_id), __import__("uuid").UUID(user_id)
    )


@router.get("/connect", response_model=GoogleConnectResponse, dependencies=_AUTH)
async def connect_google(service: GoogleOAuthService = Depends(_get_service)):
    configured, missing = google_oauth_config_status()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Google OAuth is not configured on this environment. "
                f"Missing: {', '.join(missing)}"
            ),
        )
    try:
        auth_url, state = service.generate_authorization_url()
        return GoogleConnectResponse(authorization_url=auth_url, state=state)
    except GoogleOAuthError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception:
        logger.exception("google_connect.failed")
        raise HTTPException(
            status_code=500, detail="Failed to generate authorization URL"
        ) from None  # noqa: E501


@router.get("/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
):
    """Google redirects here without a Bearer token — auth is via OAuth state."""
    import hashlib
    from uuid import UUID

    from app.modules.communication_hub.service import _OAUTH_STATE_STORE

    state_hash = hashlib.sha256(state.encode()).hexdigest()
    state_data = _OAUTH_STATE_STORE.get(state_hash)
    if not state_data:
        return RedirectResponse(
            url=_frontend_integrations_url(google="error", reason="invalid_state"),
            status_code=302,
        )

    tenant_id = UUID(state_data["tenant_id"])
    user_id = UUID(state_data["user_id"])

    service = GoogleOAuthService(db, tenant_id, user_id)
    try:
        account = await service.handle_callback(code, state)
        # Kick off Gmail + Calendar sync immediately after connect (non-blocking).
        from app.modules.communication_hub.initial_sync import schedule_initial_sync

        schedule_initial_sync(tenant_id, user_id)
        return RedirectResponse(
            url=_frontend_integrations_url(
                google="connected",
                email=account.email or "",
                tab="integrations",
                sync="started",
            ),
            status_code=302,
        )
    except GoogleOAuthError as e:
        logger.warning("google_callback.failed", extra={"error": str(e)})
        return RedirectResponse(
            url=_frontend_integrations_url(
                google="error", reason="oauth_failed", tab="integrations"
            ),
            status_code=302,
        )
    except Exception:
        logger.exception("google_callback.error")
        return RedirectResponse(
            url=_frontend_integrations_url(
                google="error", reason="server_error", tab="integrations"
            ),
            status_code=302,
        )


@router.get("/status", response_model=GoogleStatusResponse, dependencies=_AUTH)
async def google_status(service: GoogleOAuthService = Depends(_get_service)):
    configured, missing = google_oauth_config_status()
    connected, account = await service.get_status()
    if not connected or not account:
        return GoogleStatusResponse(
            connected=False,
            oauth_configured=configured,
            config_missing=missing,
        )

    scopes_granted = (account.scope or "").split()
    # Sync is possible when access token is fresh OR a refresh token can renew it.
    token_valid = bool(account.refresh_token_encrypted)
    if account.token_expiry:
        from datetime import datetime, timedelta

        skew = datetime.now(UTC) + timedelta(seconds=60)
        if account.token_expiry > skew:
            token_valid = True

    return GoogleStatusResponse(
        connected=True,
        account=GoogleAccountResponse.model_validate(account),
        scopes_granted=scopes_granted,
        token_valid=token_valid,
        oauth_configured=configured,
        config_missing=missing,
    )


@router.post("/disconnect", response_model=GoogleDisconnectResponse, dependencies=_AUTH)
async def disconnect_google(service: GoogleOAuthService = Depends(_get_service)):
    success = await service.disconnect()
    if not success:
        return GoogleDisconnectResponse(
            success=False,
            message="No active Google connection found",
        )
    return GoogleDisconnectResponse(
        success=True,
        message="Google account disconnected successfully",
    )


@router.post("/sync", response_model=GoogleSyncResponse, dependencies=_AUTH)
async def sync_gmail(
    request: GoogleSyncRequest = GoogleSyncRequest(),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    from uuid import UUID

    from app.modules.communication_hub.gmail_sync import GmailSyncError, GmailSyncService

    service = GmailSyncService(db, UUID(tenant_id), UUID(user_id))
    try:
        result = await service.sync(
            days_lookback=request.days_lookback,
            max_results=request.max_results,
        )
        return GoogleSyncResponse(
            success=True,
            synced_count=result["synced_count"],
            new_count=result["new_count"],
            updated_count=result["updated_count"],
            errors=result["errors"],
            message=f"Synced {result['synced_count']} emails ({result['new_count']} new, {result['updated_count']} updated)",  # noqa: E501
        )
    except GmailSyncError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        logger.exception("gmail_sync.failed")
        raise HTTPException(status_code=500, detail="Gmail sync failed") from None


@router.post("/calendar-sync", response_model=GoogleCalendarSyncResponse, dependencies=_AUTH)
async def sync_calendar(
    request: GoogleCalendarSyncRequest = GoogleCalendarSyncRequest(),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    from uuid import UUID

    from app.modules.communication_hub.calendar_sync import CalendarSyncError, CalendarSyncService

    service = CalendarSyncService(db, UUID(tenant_id), UUID(user_id))
    try:
        result = await service.sync(
            days_lookback=request.days_lookback,
            days_forward=request.days_forward,
        )
        return GoogleCalendarSyncResponse(
            success=True,
            synced_count=result["synced_count"],
            new_count=result["new_count"],
            updated_count=result["updated_count"],
            cancelled_count=result["cancelled_count"],
            errors=result["errors"],
            message=(
                f"Synced {result['synced_count']} events "
                f"({result['new_count']} new, {result['updated_count']} updated, "
                f"{result['cancelled_count']} cancelled)"
            ),
        )
    except CalendarSyncError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        logger.exception("calendar_sync.failed")
        raise HTTPException(status_code=500, detail="Calendar sync failed") from None
