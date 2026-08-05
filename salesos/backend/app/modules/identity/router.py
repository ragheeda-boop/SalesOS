import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.rate_limit import check_rate_limit_by_key
from app.config import settings
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_db_session,
    require_permission_dep,
)
from sdk.permissions import PermissionAction

from .schemas import (
    CsrfTokenResponse,
    InviteUserRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    PasswordChangeRequest,
    RefreshTokenRequest,
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
# FE-SEC-02 — distinct from FE legacy non-httpOnly `access_token` document cookie.
ACCESS_COOKIE = "salesos_access"


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


def _set_access_cookie(response: Response, token: str) -> None:
    """Optional httpOnly access JWT for Next middleware dual-read (flag-gated)."""
    if not settings.feature_httponly_access_cookie:
        return
    max_age = settings.jwt_access_token_expire_minutes * 60
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="strict",
        secure=True,
        path="/",
    )


def _clear_access_cookie(response: Response) -> None:
    """Always attempt clear — harmless if cookie absent or flag was off."""
    response.delete_cookie(
        key=ACCESS_COOKIE,
        path="/",
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


async def get_register_db():
    """Log register_enter BEFORE get_db checkout/set_config (pre-handler hangs)."""
    import logging
    import sys

    from app.database import get_db

    log = logging.getLogger("salesos.identity.register")
    log.info("register_enter")
    sys.stdout.flush()
    async for session in get_db():
        yield session


def get_register_service(
    request: Request,
    db: AsyncSession = Depends(get_register_db),
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
    _: None = Depends(require_permission_dep("tenant", PermissionAction.ADMIN)),
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
    caller_tenant_id: str = Depends(get_current_tenant_id),
    _: None = Depends(require_permission_dep("tenant", PermissionAction.READ)),
):
    # App-layer tenant assert — tenants table has no RLS; prevent cross-tenant metadata IDOR.
    if str(tenant_id) != str(caller_tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
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
    service: IdentityService = Depends(get_register_service),
    db: AsyncSession = Depends(get_register_db),
):
    import logging
    import sys
    import time as _time

    from sqlalchemy import text as sa_text

    from app.database import abort_db_session, set_current_tenant_id

    log = logging.getLogger("salesos.identity.register")
    # get_register_db already emitted register_enter before checkout.
    log.info("register_handler join=%s", bool(body.tenant_id))
    sys.stdout.flush()
    t0 = _time.monotonic()
    steps: list[str] = []

    def _mark(step: str) -> None:
        steps.append(f"{step}={(_time.monotonic() - t0) * 1000:.0f}ms")
        log.info("register_step step=%s steps=%s", step, ",".join(steps))
        sys.stdout.flush()

    async def _bounded_exec(step: str, awaitable, timeout: float):
        """wait_for + force-terminate connection if asyncpg ignores cancel."""
        try:
            return await asyncio.wait_for(awaitable, timeout=timeout)
        except TimeoutError:
            log.error("register_timeout step=%s steps=%s", step, ",".join(steps))
            sys.stdout.flush()
            await abort_db_session(db)
            raise

    tenant_id = str(body.tenant_id) if body.tenant_id else str(uuid4())
    # RLS on users/device_sessions (FORCE) requires app.tenant_id GUC before
    # INSERT/SELECT. Self-service register has no JWT yet — pin GUC to the
    # tenant being created/joined so WITH CHECK and email uniqueness work.
    set_current_tenant_id(tenant_id)
    try:
        await _bounded_exec(
            "set_config",
            db.execute(
                sa_text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_id},
            ),
            5.0,
        )
        # PG-side kill switch for subsequent statements on this txn.
        await _bounded_exec(
            "statement_timeout",
            db.execute(sa_text("SELECT set_config('statement_timeout', '8000', true)")),
            3.0,
        )
        _mark("set_config")
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="register.set_config_timeout — check DB connectivity / pool",
        ) from exc
    if not body.tenant_id:
        # Raw INSERT — avoid ORM flush + relationship load (Railway hang/OOM).
        try:
            await _bounded_exec(
                "tenant_insert",
                db.execute(
                    sa_text(
                        "INSERT INTO tenants ("
                        "id, name, slug, plan, is_active, provisioning_status, "
                        "created_at, updated_at"
                        ") VALUES ("
                        "CAST(:id AS uuid), :name, :slug, 'free', true, 'pending', "
                        "NOW(), NOW()"
                        ")"
                    ),
                    {
                        "id": tenant_id,
                        "name": body.full_name,
                        "slug": tenant_id[:8],
                    },
                ),
                8.0,
            )
            _mark("tenant_insert")
        except TimeoutError as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "register.tenant_insert_timeout — DB lock or uncancellable "
                    "await; see register_timeout step=tenant_insert"
                ),
            ) from exc
        except Exception as exc:
            log.exception("register_tenant_insert_failed steps=%s", ",".join(steps))
            sys.stdout.flush()
            raise HTTPException(
                status_code=503,
                detail=f"register.tenant_insert_failed: {type(exc).__name__}",
            ) from exc
    else:
        _mark("tenant_provided")
    try:
        user = await service.create_user(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            full_name_ar=body.full_name_ar,
            tenant_id=tenant_id,
            defer_side_effects=True,
        )
        _mark("create_user")
    except TimeoutError as exc:
        log.error("register_timeout step=create_user steps=%s err=%s", ",".join(steps), exc)
        sys.stdout.flush()
        await abort_db_session(db)
        raise HTTPException(
            status_code=503,
            detail=f"register.user_timeout: {exc}",
        ) from exc
    uid = str(user.id)
    tid = str(user.tenant_id)
    try:
        refresh_token, family_id, family_pk, jti = await _bounded_exec(
            "token_family",
            service.create_token_family(uid, tid),
            8.0,
        )
        _mark("token_family")
        device_name, device_type = _parse_device_info(request)
        await _bounded_exec(
            "device_session",
            service.create_device_session(
                user_id=uid,
                tenant_id=tid,
                refresh_family_id=family_pk,
                device_name=device_name,
                device_type=device_type,
                ip_address=request.client.host if request.client else "",
            ),
            8.0,
        )
        _mark("device_session")
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="register.token_session_timeout",
        ) from exc
    access_token = create_access_token(uid, tid)
    _mark("access_token")
    max_age = settings.jwt_refresh_token_expire_days * 86400
    _set_refresh_cookie(response, refresh_token, max_age)
    _set_access_cookie(response, access_token)
    # Commit BEFORE response so get_db's exit commit cannot hang the 201.
    # Do NOT create_task side effects on this session (races commit → hang).
    try:
        await _bounded_exec("commit", db.commit(), 8.0)
        _mark("commit")
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="register.commit_timeout",
        ) from exc
    _mark("done")
    log.info("register_ok steps=%s", ",".join(steps))
    sys.stdout.flush()
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
        user_id=uid,
        tenant_id=tid,
        refresh_family_id=family_pk,
        device_name=device_name,
        device_type=device_type,
        ip_address=request.client.host if request.client else "",
    )
    access_token = create_access_token(uid, tid)
    max_age = settings.jwt_refresh_token_expire_days * 86400
    _set_refresh_cookie(response, refresh_token, max_age)
    _set_access_cookie(response, access_token)
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
    _: None = Depends(require_permission_dep("user", PermissionAction.READ)),
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
    _: None = Depends(require_permission_dep("user", PermissionAction.CREATE)),
):
    import secrets

    temp_password = secrets.token_urlsafe(12)
    user = await service.create_user(
        email=body.email,
        password=temp_password,
        full_name=body.email.split("@")[0],
        tenant_id=tenant_id,
    )
    role = getattr(body, "role", None) or "user"
    if role and role != getattr(user, "role", "user"):
        try:
            user = await service.update_user_role(str(user.id), role)
        except Exception:
            # Role update is best-effort; account still created.
            pass
    return {
        "message": (
            f"User account created for {body.email}. "
            "Email delivery is not configured — share temporary credentials out of band."
        ),
        "user_id": str(user.id),
        "email": body.email,
        "role": getattr(user, "role", role),
        "email_delivery": "not_configured",
        "temporary_password": temp_password,
    }


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
    from sqlalchemy import text as sa_text

    from app.database import set_current_tenant_id

    token = _extract_refresh_token(request, body)
    payload = decode_refresh_token(token)
    uid = payload["sub"]
    tid = str(payload["tenant_id"])
    jti = payload["jti"]
    # Category B5 FORCE RLS on refresh_token_families (join users): unset GUC
    # fails closed. Refresh has no Bearer; pin tenant from refresh JWT claims
    # (same pattern as authenticate() email probe) before family lookup.
    set_current_tenant_id(tid)
    await service.db.execute(
        sa_text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": tid},
    )
    blacklisted = await service.is_token_blacklisted(jti)
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token revoked")
    new_access, new_refresh = await service.rotate_refresh_token(jti, uid, tid)
    old_exp = (
        datetime.fromtimestamp(payload["exp"], tz=UTC) if "exp" in payload else datetime.now(UTC)
    )
    await service.blacklist_token(jti, "refresh", old_exp)
    max_age = settings.jwt_refresh_token_expire_days * 86400
    _set_refresh_cookie(response, new_refresh, max_age)
    _set_access_cookie(response, new_access)
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
                # FE-SEC-03: assert refresh subject matches authenticated user
                if str(payload.get("sub", "")) == str(user_id):
                    jti = payload["jti"]
                    old_exp = (
                        datetime.fromtimestamp(payload["exp"], tz=UTC)
                        if "exp" in payload
                        else datetime.now(UTC)
                    )
                    await service.blacklist_token(jti, "refresh", old_exp)
                    family_revoked = await service.revoke_by_refresh_jti(jti, user_id)
                    revoked = max(1, family_revoked)
            except Exception:
                pass
    _clear_refresh_cookie(response)
    _clear_access_cookie(response)
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
    _clear_access_cookie(response)
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
    await check_rate_limit_by_key(f"forgot-pw:{body.email.lower().strip()}", limit=3, window=900)
    token = await service.forgot_password(body.email)
    response: dict = {"message": "If the email exists, a reset token has been generated"}
    if token is not None and settings.env != "production":
        response["token"] = token
    return response


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    service: IdentityService = Depends(get_service),
):
    from .schemas import validate_password_strength

    validate_password_strength(body.new_password)
    await service.reset_password(body.token, body.new_password)
    return {"message": "Password reset successfully"}


@router.delete("/users/me", status_code=200)
async def delete_my_account(
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    """PDPL Right to Erasure — permanently delete my account and anonymize personal data."""
    await service.delete_user(user_id, tenant_id)
    return {"message": "تم حذف الحساب بنجاح", "detail": "Account deleted per PDPL right to erasure"}


@router.get("/.well-known/jwks.json")
async def jwks():
    """JWKS endpoint for JWT key discovery.

    Returns RSA public key for RS256 token verification.
    """
    from app.modules.identity.jwks import get_jwks

    return get_jwks()
