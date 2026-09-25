"""Development-only HTML login. Same-origin via Next rewrite so localStorage works.

Cursor's embedded browser intercepts /login and posts NextAuth credentials with
the wrong email (401 in ~6ms). This page is not a native password-manager form
target for that flow. Same authenticate() as /login. Not Production GO.
"""

from __future__ import annotations

import html
import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.common.exceptions import UnauthorizedError
from app.config import settings
from app.modules.identity.router import (
    _parse_device_info,
    get_service,
)
from app.modules.identity.service import IdentityService, create_access_token

router = APIRouter()

_DEFAULT_EMAIL = "pif.local@salesos.io"
_NEXT = "/v3/companies"


def _allowed() -> bool:
    env = (settings.env or "").strip().lower()
    return env not in {"production", "prod", "staging", "stage"}


def _page(email: str, error: str = "") -> str:
    err = (
        f'<p role="alert" style="color:#b91c1c;font-size:14px">{html.escape(error)}</p>'
        if error
        else ""
    )
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>دخول محلي — SalesOS</title>
</head>
<body style="font-family:system-ui,sans-serif;max-width:420px;margin:48px auto;padding:0 16px">
  <h1 style="font-size:20px">دخول محلي (docker)</h1>
  <p style="color:#555;font-size:14px">
    ليس Production GO. استخدم حساب <code>pif.local@salesos.io</code>
    وكلمة المرور من الملف المحلي <code>W4_PIF_LOCAL_USER.json</code>.
  </p>
  {err}
  <form method="post" action="/api/v1/identity/local-login" autocomplete="off" data-local-login="1">
    <label style="display:block;margin:12px 0 4px">البريد</label>
    <input name="email" type="text" inputmode="email" value="{html.escape(email)}"
           required style="width:100%;padding:8px;box-sizing:border-box"/>
    <label style="display:block;margin:12px 0 4px">كلمة المرور</label>
    <input name="password" type="password" required autocomplete="off"
           style="width:100%;padding:8px;box-sizing:border-box"/>
    <button type="submit" style="margin-top:16px;width:100%;padding:10px">دخول</button>
  </form>
</body>
</html>"""


def _handoff(access_token: str, refresh_token: str, tenant_id: str) -> str:
    payload = json.dumps(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "tenant_id": tenant_id,
            "next": _NEXT,
        },
        ensure_ascii=False,
    )
    return f"""<!doctype html>
<html lang="ar">
<head><meta charset="utf-8"/><title>جاري الدخول…</title></head>
<body>
<p>جاري فتح الشركات…</p>
<script>
const s = {payload};
try {{
  localStorage.setItem("access_token", s.access_token);
  localStorage.setItem("refresh_token", s.refresh_token);
  localStorage.setItem("tenant_id", s.tenant_id);
  document.cookie = "access_token=" + encodeURIComponent(s.access_token) + "; path=/; SameSite=Lax; max-age=86400";
}} catch (e) {{}}
window.location.replace(s.next);
</script>
</body>
</html>"""


@router.get("/local-login", response_class=HTMLResponse)
async def local_login_form():
    if not _allowed():
        raise HTTPException(status_code=404, detail="Not found")
    return HTMLResponse(_page(_DEFAULT_EMAIL))


@router.post("/local-login", response_class=HTMLResponse)
async def local_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    service: IdentityService = Depends(get_service),
):
    if not _allowed():
        raise HTTPException(status_code=404, detail="Not found")
    try:
        user = await service.authenticate(email=email.strip(), password=password)
    except UnauthorizedError as exc:
        return HTMLResponse(_page(email.strip() or _DEFAULT_EMAIL, str(exc.detail)), status_code=401)

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
    resp = HTMLResponse(_handoff(access_token, refresh_token, tid))
    cookie_age = settings.jwt_access_token_expire_minutes * 60
    secure = (settings.env or "").strip().lower() in {"production", "prod", "staging", "stage"}
    resp.set_cookie(
        key="access_token",
        value=access_token,
        max_age=cookie_age,
        httponly=False,
        samesite="lax",
        secure=secure,
        path="/",
    )
    resp.set_cookie(
        key="tenant_id",
        value=tid,
        max_age=cookie_age,
        httponly=False,
        samesite="lax",
        secure=secure,
        path="/",
    )
    return resp
