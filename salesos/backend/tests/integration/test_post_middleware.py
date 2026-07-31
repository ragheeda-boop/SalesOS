from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.common.middleware import BodyCacheMiddleware
from app.routers.metrics import MetricsMiddleware


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


def _make_app(max_body_size: int = 10 * 1024 * 1024) -> FastAPI:
    """Build a minimal app with the real middleware chain + a POST echo route."""
    app = FastAPI()

    # Register a global exception handler (same as main.py)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    # Add middleware in same order as production
    app.add_middleware(MetricsMiddleware)

    from app.modules.api_keys.middleware import ApiKeyMiddleware
    from app.modules.audit.middleware import AuditMiddleware

    # Mock the session factory to avoid PostgreSQL dependency in tests
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__ = AsyncMock()
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    app.add_middleware(AuditMiddleware, session_factory=mock_session_factory)
    app.add_middleware(ApiKeyMiddleware)
    app.add_middleware(BodyCacheMiddleware, max_body_size=max_body_size)

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
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",  # noqa: E501
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
        responses = await asyncio.gather(
            *[
                client.post(
                    "/api/v1/echo",
                    json={"seq": i},
                    headers={"X-Tenant-Id": "tenant-1"},
                    timeout=10,
                )
                for i in range(10)
            ]
        )
    assert all(r.status_code == 200 for r in responses)
    for i, r in enumerate(responses):
        assert r.json()["received"]["seq"] == i


@pytest.mark.asyncio
async def test_oversized_body_returns_413():
    """POST with body exceeding max_body_size should return 413."""
    app = _make_app(max_body_size=1024)  # 1KB limit for test
    transport = ASGITransport(app=app)
    large_body = {"data": "x" * 2000}  # ~2KB when serialized
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/echo",
            json=large_body,
            headers={"X-Tenant-Id": "tenant-1"},
            timeout=10,
        )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


@pytest.mark.asyncio
async def test_body_cache_available_in_request_state():
    """BodyCacheMiddleware should store body in scope['body_cache']."""
    app = _make_app()
    transport = ASGITransport(app=app)

    @app.post("/api/v1/check-cache")
    async def check_cache(request: Request):
        cached = request.scope.get("body_cache", b"")
        return JSONResponse(
            content={"cached_length": len(cached), "cached_type": type(cached).__name__}
        )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/check-cache",
            json={"test": True},
            headers={"X-Tenant-Id": "tenant-1"},
            timeout=5,
        )
    assert response.status_code == 200
    assert response.json()["cached_length"] > 0
    assert response.json()["cached_type"] == "bytes"


@pytest.mark.asyncio
async def test_multiple_receive_calls_after_cache():
    """After body is cached, subsequent receive() calls should return disconnect."""
    app = _make_app()

    @app.post("/api/v1/double-receive")
    async def double_receive(request: Request):
        # First call should return cached body
        msg1 = await request.receive()
        assert msg1["type"] == "http.request"
        assert msg1["more_body"] is False
        assert len(msg1["body"]) > 0

        # Second call should return disconnect
        msg2 = await request.receive()
        return JSONResponse(content={"msg2_type": msg2["type"]})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/double-receive",
            json={"test": True},
            headers={"X-Tenant-Id": "tenant-1"},
            timeout=5,
        )
    assert response.status_code == 200
    assert response.json()["msg2_type"] == "http.disconnect"


@pytest.mark.asyncio
async def test_concurrent_post_different_bodies():
    """Concurrent POST requests with different bodies should not mix."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(
            *[
                client.post(
                    "/api/v1/echo",
                    json={"id": i, "unique": f"data_{i}"},
                    headers={"X-Tenant-Id": "tenant-1"},
                    timeout=10,
                )
                for i in range(20)
            ]
        )
    assert all(r.status_code == 200 for r in responses)
    for i, r in enumerate(responses):
        data = r.json()["received"]
        assert data["id"] == i
        assert data["unique"] == f"data_{i}"
