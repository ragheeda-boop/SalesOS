from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_current_tenant_id, get_db_session, verify_token

from .service import ApiKeyService

router = APIRouter()


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    expiry_days: int | None = Field(None, ge=1, le=3650)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: list[str]
    expires_at: str | None
    last_used_at: str | None
    created_at: str | None


class CreateApiKeyResponse(BaseModel):
    id: str
    name: str
    api_key: str
    key_prefix: str
    expires_at: str | None


def get_service(request: Request, db: AsyncSession = Depends(get_db_session)) -> ApiKeyService:
    return ApiKeyService(db=db, logger=getattr(request.app.state, "logger", None))


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    token: dict = Depends(verify_token),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    service: ApiKeyService = Depends(get_service),
):
    api_key, raw_key = await service.create(
        tenant_id=tenant_id,
        user_id=user_id,
        name=body.name,
        scopes=body.scopes,
        expiry_days=body.expiry_days,
    )
    return CreateApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=raw_key,
        key_prefix=api_key.key_prefix,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    token: dict = Depends(verify_token),
    user_id: str = Depends(get_current_user_id),
    service: ApiKeyService = Depends(get_service),
):
    return await service.list_for_user(user_id)


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    token: dict = Depends(verify_token),
    user_id: str = Depends(get_current_user_id),
    service: ApiKeyService = Depends(get_service),
):
    ok = await service.revoke(key_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="API key not found or already revoked")
    return {"message": "API key revoked"}
