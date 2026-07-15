from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.routers.metrics import MetricsMiddleware


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


def _make_app() -> FastAPI:
    """Build a minimal app with the real middleware chain + a POST echo route."""
    app = FastAPI()

    # Register a global exception handler (same as main.py)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    # Add the three middleware that were previously BaseHTTPMiddleware
    app.add_middleware(MetricsMiddleware)

    from app.modules.audit.middleware import AuditMiddleware
    from app.modules.api_keys.middleware import ApiKeyMiddleware

    app.add_middleware(AuditMiddleware)
    app.add_middleware(ApiKeyMiddleware)

    # Echo route that returns the request body
    @app.post("/api/v1/echo")
    async def echo(request: Request):
        body = await request.json()
        return JSONResponse(content={"received": body})

    @app.post("/api/v1/form")
    async def form_echo(request: Request):
        form = await request.form()
        return JSONResponse(content={"received": dict(form)})

    @app.post("/api/v1/empty")
    async def empty_post(request: Request):
        body = await request.body()
        return JSONResponse(content={"received_length": len(body)})

    @app.get("/api/v1/ping")
    async def ping():
        return JSONResponse(content={"ok": True})

    return app


@pytest.mark.asyncio
async def test_post_json_body():
    """POST with JSON body should not hang."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/echo",
            json={"name": "test", "value": 42},
            headers={"X-Tenant-Id": "tenant-1"},
            timeout=5,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["received"]["name"] == "test"
    assert data["received"]["value"] == 42


@pytest.mark.asyncio
async def test_post_empty_body():
    """POST with empty body should not hang."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/empty",
            content=b"",
            headers={"X-Tenant-Id": "tenant-1"},
            timeout=5,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["received_length"] == 0


@pytest.mark.asyncio
async def test_post_form_body():
    """POST with form data should not hang."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/form",
            data={"field1": "hello", "field2": "world"},
            headers={"X-Tenant-Id": "tenant-1"},
            timeout=5,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["received"]["field1"] == "hello"
    assert data["received"]["field2"] == "world"


@pytest.mark.asyncio
async def test_post_with_auth_header():
    """POST with Bearer auth should not hang."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/echo",
            json={"status": "authorized"},
            headers={
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "X-Tenant-Id": "tenant-1",
            },
            timeout=5,
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_request_still_works():
    """GET requests should remain unaffected."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ping", timeout=5)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_large_json_body():
    """POST with a large JSON body should not hang."""
    app = _make_app()
    transport = ASGITransport(app=app)
    large_body = {f"key_{i}": f"value_{i}" for i in range(100)}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/echo",
            json=large_body,
            headers={"X-Tenant-Id": "tenant-1"},
            timeout=10,
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["received"]) == 100


@pytest.mark.asyncio
async def test_concurrent_post_requests():
    """Multiple concurrent POST requests should all complete."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(*[
            client.post(
                "/api/v1/echo",
                json={"seq": i},
                headers={"X-Tenant-Id": "tenant-1"},
                timeout=10,
            )
            for i in range(10)
        ])
    assert all(r.status_code == 200 for r in responses)
    for i, r in enumerate(responses):
        assert r.json()["received"]["seq"] == i
