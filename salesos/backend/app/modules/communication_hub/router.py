"""Google Workspace integration router — Communication Hub.

Endpoints:
  GET  /api/v1/integrations/google/connect    — Start OAuth flow
  GET  /api/v1/integrations/google/callback   — OAuth callback (no auth required)
  GET  /api/v1/integrations/google/status     — Connection status
  POST /api/v1/integrations/google/disconnect — Disconnect account
"""
import hashlib
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_db_session,
    verify_token,
)
from app.modules.communication_hub.schemas import (
    GoogleAccountResponse,
    GoogleConnectResponse,
    GoogleDisconnectResponse,
    GoogleStatusResponse,
)
from app.modules.communication_hub.service import (
    GoogleOAuthError,
    GoogleOAuthService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/google", tags=["Google Workspace"])


def _get_service(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
) -> GoogleOAuthService:
    return GoogleOAuthService(db, UUID(tenant_id), UUID(user_id))


@router.get(
    "/connect",
    response_model=GoogleConnectResponse,
    dependencies=[Depends(verify_token)],
)
async def connect_google(service: GoogleOAuthService = Depends(_get_service)):
    try:
        auth_url, state = service.generate_authorization_url()
        return GoogleConnectResponse(authorization_url=auth_url, state=state)
    except Exception:
        logger.exception("google_connect.failed")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")


@router.get("/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
):
    from app.modules.communication_hub.service import _OAUTH_STATE_STORE

    state_hash = hashlib.sha256(state.encode()).hexdigest()
    state_data = _OAUTH_STATE_STORE.get(state_hash)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    tenant_id = UUID(state_data["tenant_id"])
    user_id = UUID(state_data["user_id"])

    service = GoogleOAuthService(db, tenant_id, user_id)
    try:
        account = await service.handle_callback(code, state)
        return {
            "status": "connected",
            "email": account.email,
            "provider": account.provider,
        }
    except GoogleOAuthError as e:
        logger.warning("google_callback.failed", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("google_callback.error")
        raise HTTPException(status_code=500, detail="OAuth callback processing failed")


@router.get(
    "/status",
    response_model=GoogleStatusResponse,
    dependencies=[Depends(verify_token)],
)
async def google_status(service: GoogleOAuthService = Depends(_get_service)):
    connected, account = await service.get_status()
    if not connected or not account:
        return GoogleStatusResponse(connected=False)

    scopes_granted = (account.scope or "").split()
    token_valid = False
    if account.token_expiry:
        token_valid = account.token_expiry > datetime.now(timezone.utc)

    return GoogleStatusResponse(
        connected=True,
        account=GoogleAccountResponse.model_validate(account),
        scopes_granted=scopes_granted,
        token_valid=token_valid,
    )


@router.post(
    "/disconnect",
    response_model=GoogleDisconnectResponse,
    dependencies=[Depends(verify_token)],
)
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
