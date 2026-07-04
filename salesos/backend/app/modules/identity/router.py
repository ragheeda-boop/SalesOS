from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session

from pydantic import BaseModel, Field

from .schemas import (
    InviteUserRequest,
    LoginRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RoleUpdateRequest,
    TenantCreate,
    TenantResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from .service import IdentityService, create_access_token, create_refresh_token, decode_access_token, decode_refresh_token


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

router = APIRouter()


def get_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> IdentityService:
    return IdentityService(
        db=db,
        event_bus=getattr(request.app.state, "event_bus", None),
        logger=getattr(request.app.state, "logger", None),
    )


@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreate,
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    tenant = await service.create_tenant(
        name=body.name,
        slug=body.slug,
        domain=body.domain,
    )
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        domain=tenant.domain,
        plan=tenant.plan,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    service: IdentityService = Depends(get_service),
):
    tenant = await service.get_tenant(tenant_id)
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        domain=tenant.domain,
        plan=tenant.plan,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: UserCreate,
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    tenant_id = str(body.tenant_id) if body.tenant_id else str(uuid4())
    if not body.tenant_id:
        from app.modules.identity.models import Tenant
        tenant = Tenant(id=tenant_id, name=body.full_name, slug=tenant_id[:8], plan="free")
        db.add(tenant)
        await db.flush()
    user = await service.create_user(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        full_name_ar=body.full_name_ar,
        tenant_id=tenant_id,
    )
    access_token = create_access_token(str(user.id), str(user.tenant_id))
    refresh_token = create_refresh_token(str(user.id), str(user.tenant_id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30,
        tenant_id=str(user.tenant_id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    user = await service.authenticate(email=body.email, password=body.password)
    access_token = create_access_token(str(user.id), str(user.tenant_id))
    refresh_token = create_refresh_token(str(user.id), str(user.tenant_id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30,
        tenant_id=str(user.tenant_id),
    )


@router.get("/users/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    user = await service.get_user(user_id)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        full_name_ar=user.full_name_ar,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        tenant_id=user.tenant_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    tenant_id: str = Depends(get_current_tenant_id),
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    users = await service.get_users_by_tenant(tenant_id)
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            full_name_ar=u.full_name_ar,
            role=u.role,
            is_active=u.is_active,
            is_verified=u.is_verified,
            tenant_id=u.tenant_id,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]


@router.post("/invite", status_code=201)
async def invite_user(
    body: InviteUserRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    import secrets
    temp_password = secrets.token_urlsafe(12)
    user = await service.create_user(
        email=body.email,
        password=temp_password,
        full_name=body.email.split("@")[0],
        tenant_id=tenant_id,
    )
    return {"message": f"User {body.email} invited successfully", "user_id": str(user.id)}


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    user_id: str = Depends(get_current_user_id),
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    await service.change_password(user_id, body.current_password, body.new_password)
    return {"message": "Password changed successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
):
    payload = decode_refresh_token(body.refresh_token)
    access_token = create_access_token(payload["sub"], payload["tenant_id"])
    new_refresh = create_refresh_token(payload["sub"], payload["tenant_id"])
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=30,
    )


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    service: IdentityService = Depends(get_service),
):
    await service.forgot_password(body.email)
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    service: IdentityService = Depends(get_service),
):
    await service.reset_password(body.token, body.new_password)
    return {"message": "Password reset successfully"}
