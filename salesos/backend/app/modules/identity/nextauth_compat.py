"""Local login alias for clients that POST NextAuth's credentials URL.

Cursor's embedded browser posts ``/api/auth/callback/credentials`` (CSRF 403
via the FastAPI rewrite). This path reuses IdentityService.authenticate —
same password / lockout / token family as ``POST /api/v1/identity/login``.
Does not skip verification. Not Production GO.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db_session
from app.modules.identity.router import (
    _parse_device_info,
    _set_access_cookie,
    _set_refresh_cookie,
    get_service,
)
from app.modules.identity.service import IdentityService, create_access_token

router = APIRouter()


def _safe_next(raw: str | None) -> str:
    path = (raw or "/v3").strip()
    if not path.startswith("/") or path.startswith("//"):
        return "/v3"
    if path.startswith("/login") or path.startswith("/admin/login"):
        return "/v3"
    return path


def _cookie_secure() -> bool:
    return (settings.env or "").strip().lower() in {"production", "prod", "staging", "stage"}


async def _read_credentials(request: Request) -> tuple[str, str, str, bool]:
    content_type = (request.headers.get("content-type") or "").lower()
    email = password = callback = ""
    wants_json = "application/json" in (request.headers.get("accept") or "").lower()
    if "application/json" in content_type:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
        email = str(body.get("email") or body.get("username") or "").strip()
        password = str(body.get("password") or "")
        callback = str(body.get("callbackUrl") or body.get("callback_url") or "")
        wants_json = True
    else:
        form = await request.form()
        email = str(form.get("email") or form.get("username") or "").strip()
        password = str(form.get("password") or "")
        callback = str(form.get("callbackUrl") or form.get("callback_url") or "")
        wants_json = wants_json or str(form.get("json") or "").lower() in {"true", "1"}
    return email, password, _safe_next(callback), wants_json


def _attach_session_cookies(resp: Response, *, access_token: str, refresh_token: str, tenant_id: str) -> None:
    max_age = settings.jwt_refresh_token_expire_days * 86400
    _set_refresh_cookie(resp, refresh_token, max_age)
    _set_access_cookie(resp, access_token)
    # Middleware reads the FE `access_token` cookie. Main login leaves this to JS;
    # this alias must set it because Cursor never runs persistAuthTokens.
    cookie_age = settings.jwt_access_token_expire_minutes * 60
    resp.set_cookie(
        key="access_token",
        value=access_token,
        max_age=cookie_age,
        httponly=False,
        samesite="lax",
        secure=_cookie_secure(),
        path="/",
    )
    resp.set_cookie(
        key="tenant_id",
        value=tenant_id,
        max_age=cookie_age,
        httponly=False,
        samesite="lax",
        secure=_cookie_secure(),
        path="/",
    )


@router.post("/callback/credentials")
async def credentials_callback(
    request: Request,
    service: IdentityService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
):
    email, password, nxt, wants_json = await _read_credentials(request)
    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail=(
                "Use http://localhost:3000/login and POST /api/v1/identity/login. | "
                "سجّل الدخول من /login."
            ),
        )

    if service.logger:
        service.logger.info("auth.credentials_alias_attempt", email=email)
    user = await service.authenticate(email=email, password=password)
    uid = str(user.id)
    tid = str(user.tenant_id)
    refresh_token, _family_id, family_pk, _jti = await service.create_token_family(uid, tid)
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
    payload = {
        "ok": True,
        "url": nxt,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "tenant_id": tid,
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }
    if wants_json:
        resp: Response = JSONResponse(payload)
    else:
        resp = RedirectResponse(url=nxt, status_code=303)
    _attach_session_cookies(resp, access_token=access_token, refresh_token=refresh_token, tenant_id=tid)
    return resp
