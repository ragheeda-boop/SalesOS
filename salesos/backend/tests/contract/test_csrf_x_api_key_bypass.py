"""HTTP regression for Phase 0 criterion 1.3 / PROD-W5-001 / STORY-01-03.

Bare ``X-API-Key`` and authenticated API-key state must not bypass CSRF on
state-changing methods. Unit coverage lives in ``TestCsrfMiddleware``; this
file proves the same rule over FastAPI + httpx ASGI.

Does not modify get_db() / set_config (DEC-085).
"""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.common.middleware import CsrfEnforcementMiddleware


class _ForceApiKeyAuthenticated:
    """Outer middleware: set api_key_authenticated before CSRF runs."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            Request(scope, receive).state.api_key_authenticated = True
        await self.app(scope, receive, send)


def _csrf_app(*, force_api_key_auth: bool = False) -> FastAPI:
    app = FastAPI()

    @app.post("/api/v1/echo")
    async def echo() -> JSONResponse:
        return JSONResponse({"ok": True})

    # Starlette: last add_middleware = outermost (runs first on ingress).
    app.add_middleware(CsrfEnforcementMiddleware)
    if force_api_key_auth:
        app.add_middleware(_ForceApiKeyAuthenticated)
    return app


@pytest.fixture(autouse=True)
def _csrf_enforcement_on():
    previous = os.environ.pop("SALESOS_TESTING", None)
    yield
    if previous is None:
        os.environ["SALESOS_TESTING"] = "true"
    else:
        os.environ["SALESOS_TESTING"] = previous


@pytest.mark.asyncio
async def test_post_with_bare_x_api_key_returns_403():
    """Non-empty X-API-Key alone must not skip CSRF (PROD-W5-001)."""
    transport = ASGITransport(app=_csrf_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/echo",
            json={"n": 1},
            headers={"X-API-Key": "sos_fake_unverified"},
        )
    assert response.status_code == 403
    assert "CSRF" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_post_with_authenticated_api_key_still_requires_csrf():
    """Authenticated API-key state must NOT bypass CSRF (STORY-01-03 / 1.3)."""
    transport = ASGITransport(app=_csrf_app(force_api_key_auth=True))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/echo",
            json={"n": 1},
            headers={"X-API-Key": "sos_valid"},
        )
    assert response.status_code == 403
    assert "CSRF" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_post_with_matching_csrf_passes_even_with_api_key_auth():
    transport = ASGITransport(app=_csrf_app(force_api_key_auth=True))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/echo",
            json={"n": 1},
            headers={
                "X-API-Key": "sos_valid",
                "Cookie": "csrf_token=tok-1.3",
                "X-CSRF-Token": "tok-1.3",
            },
        )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
