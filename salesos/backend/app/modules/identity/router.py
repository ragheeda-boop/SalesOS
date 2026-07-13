from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.config import settings
from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from pydantic import BaseModel, Field

from .schemas import (
    CsrfTokenResponse,
    InviteUserRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RoleUpdateRequest,
    SessionResponse,
    TenantCreate,
    TenantResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from .service import IdentityService, create_access_token, decode_refresh_token


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12, max_length=128)

router = APIRouter()

REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="strict",
        secure=True,
        path="/api/v1/identity",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE,
        path="/api/v1/identity",
        httponly=True,
        samesite="strict",
        secure=True,
    )


def _set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE,
        value=token,
        max_age=86400,
        httponly=False,
        samesite="strict",
        secure=True,
        path="/",
    )


def get_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> IdentityService:
    return IdentityService(
        db=db,
        event_bus=getattr(request.app.state, "event_bus", None),
        logger=getattr(request.app.state, "logger", None),
    )


def _extract_refresh_token(request: Request, body: RefreshTokenRequest) -> str:
    token = body.refresh_token
    if not token:
        token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    return token


def _parse_device_info(request: Request) -> tuple[str, str]:
    ua = request.headers.get("user-agent", "")
    if not ua:
        return "unknown", "unknown"
    ua_lower = ua.lower()
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        dtype = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        dtype = "tablet"
    else:
        dtype = "desktop"
    return ua[:512], dtype


@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreate,
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permission_dep(PermissionAction.ADMIN, "tenant")),
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
    _: None = Depends(require_permission_dep(PermissionAction.READ, "tenant")),
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
    request: Request,
    response: Response,
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
    uid = str(user.id)
    tid = str(user.tenant_id)
    refresh_token, family_id, family_pk, jti = await service.create_token_family(uid, tid)
    device_name, device_type = _parse_device_info(request)
    await service.create_device_session(
        user_id=uid, tenant_id=tid, refresh_family_id=family_pk,
        device_name=device_name, device_type=device_type,
        ip_address=request.client.host if request.client else "",
    )
    access_token = create_access_token(uid, tid)
    max_age = settings.jwt_refresh_token_expire_days * 86400
    _set_refresh_cookie(response, refresh_token, max_age)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        tenant_id=tid,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    user = await service.authenticate(email=body.email, password=body.password)
    uid = str(user.id)
    tid = str(user.tenant_id)
    refresh_token, family_id, family_pk, jti = await service.create_token_family(uid, tid)
    device_name, device_type = _parse_device_info(request)
    await service.create_device_session(
        user_id=uid, tenant_id=tid, refresh_family_id=family_pk,
        device_name=device_name, device_type=device_type,
        ip_address=request.client.host if request.client else "",
    )
    access_token = create_access_token(uid, tid)
    max_age = settings.jwt_refresh_token_expire_days * 86400
    _set_refresh_cookie(response, refresh_token, max_age)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        tenant_id=tid,
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
    _: None = Depends(require_permission_dep(PermissionAction.READ, "user")),
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
    _: None = Depends(require_permission_dep(PermissionAction.CREATE, "user")),
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
    request: Request,
    response: Response,
    service: IdentityService = Depends(get_service),
):
    token = _extract_refresh_token(request, body)
    payload = decode_refresh_token(token)
    uid = payload["sub"]
    tid = payload["tenant_id"]
    jti = payload["jti"]
    blacklisted = await service.is_token_blacklisted(jti)
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token revoked")
    new_access, new_refresh = await service.rotate_refresh_token(jti, uid, tid)
    old_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if "exp" in payload else datetime.now(timezone.utc)
    await service.blacklist_token(jti, "refresh", old_exp)
    max_age = settings.jwt_refresh_token_expire_days * 86400
    _set_refresh_cookie(response, new_refresh, max_age)
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        tenant_id=tid,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    body: LogoutRequest,
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user_id),
    service: IdentityService = Depends(get_service),
):
    revoked = 0
    if body.session_id:
        revoked = await service.revoke_session(body.session_id, user_id)
    elif body.all_sessions:
        revoked = await service.revoke_all_user_sessions(user_id)
    else:
        token = body.refresh_token or request.cookies.get(REFRESH_COOKIE)
        if token:
            try:
                payload = decode_refresh_token(token)
                jti = payload["jti"]
                old_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if "exp" in payload else datetime.now(timezone.utc)
                await service.blacklist_token(jti, "refresh", old_exp)
                revoked = 1
            except Exception:
                pass
    _clear_refresh_cookie(response)
    return LogoutResponse(
        message="Logged out successfully",
        sessions_revoked=revoked,
    )


@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    service: IdentityService = Depends(get_service),
):
    revoked = await service.revoke_all_user_sessions(user_id)
    _clear_refresh_cookie(response)
    return LogoutResponse(
        message="All sessions revoked",
        sessions_revoked=revoked,
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    user_id: str = Depends(get_current_user_id),
    service: IdentityService = Depends(get_service),
):
    sessions = await service.get_user_sessions(user_id)
    return [
        SessionResponse(
            id=s.id,
            device_name=s.device_name,
            device_type=s.device_type,
            ip_address=s.ip_address,
            last_used_at=s.last_used_at,
            created_at=s.created_at,
            expires_at=s.expires_at,
            is_active=not s.is_revoked,
        )
        for s in sessions
    ]


@router.post("/sessions/{session_id}/revoke", response_model=LogoutResponse)
async def revoke_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    service: IdentityService = Depends(get_service),
):
    revoked = await service.revoke_session(session_id, user_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Session not found")
    return LogoutResponse(message="Session revoked", sessions_revoked=1)


@router.get("/csrf-token", response_model=CsrfTokenResponse)
async def get_csrf_token(response: Response):
    import secrets
    token = secrets.token_urlsafe(32)
    _set_csrf_cookie(response, token)
    return CsrfTokenResponse(csrf_token=token)


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
    from .schemas import validate_password_strength
    validate_password_strength(body.new_password)
    await service.reset_password(body.token, body.new_password)
    return {"message": "Password reset successfully"}


@router.get("/.well-known/jwks.json")
async def jwks():
    """JWKS endpoint for JWT key discovery.

    Currently uses HS256 (symmetric). The kid field enables future
    key rotation. Migration path to RS256:
      1. Generate RSA key pair, add to config
      2. Add 'v2-rs256' kid entry here alongside 'v1-hs256'
      3. Rotate signer to use new kid
      4. Remove old kid after all tokens expire
    """
    return {
        "keys": [
            {
                "kty": "oct",
                "kid": "v1-hs256",
                "alg": "HS256",
                "use": "sig",
                "k": ""  # HS256 key not exposed (symmetric)
            }
        ]
    }
