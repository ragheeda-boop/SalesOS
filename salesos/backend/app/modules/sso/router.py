from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db_session

from .service import OAuthService

router = APIRouter()


def get_service(request: Request, db: AsyncSession = Depends(get_db_session)) -> OAuthService:
    return OAuthService(db=db, logger=getattr(request.app.state, "logger", None))


@router.post("/auth/sso/{provider}")
async def sso_login(
    provider: str,
    service: OAuthService = Depends(get_service),
):
    try:
        auth_url = service.get_authorization_url(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"authorization_url": auth_url}


@router.get("/auth/sso/{provider}/callback")
async def sso_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    service: OAuthService = Depends(get_service),
):
    try:
        access_token, user_id = await service.handle_callback(provider, code, state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"SSO authentication failed: {str(e)}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
    }


@router.get("/auth/sso/connections")
async def list_sso_connections(
    user_id: str = Depends(get_current_user_id),
    service: OAuthService = Depends(get_service),
):
    connections = await service.get_connections_for_user(user_id)
    return [
        {
            "provider": c.provider,
            "provider_email": c.provider_email,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in connections
    ]


@router.delete("/auth/sso/{provider}")
async def disconnect_sso(
    provider: str,
    user_id: str = Depends(get_current_user_id),
    service: OAuthService = Depends(get_service),
):
    ok = await service.disconnect_provider(user_id, provider)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No active {provider} connection found")
    return {"message": f"{provider} connection disconnected"}
