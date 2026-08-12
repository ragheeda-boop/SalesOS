"""AuditMiddleware must not hold the ASGI cycle on slow DB writes (IL-2A)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.modules.audit.middleware import AuditMiddleware


@pytest.mark.asyncio
async def test_audit_middleware_returns_before_slow_db_write():
    """POST response must complete even when audit persist hangs."""
    app = FastAPI()

    hang = asyncio.Event()

    class _SlowSessionCM:
        async def __aenter__(self):
            await hang.wait()
            return MagicMock()

        async def __aexit__(self, *args):
            return False

    mock_factory = MagicMock(side_effect=lambda: _SlowSessionCM())

    app.add_middleware(AuditMiddleware, session_factory=mock_factory)

    @app.post("/api/v1/probe")
    async def probe():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t0 = asyncio.get_running_loop().time()
        response = await client.post("/api/v1/probe", timeout=2.0)
        elapsed = asyncio.get_running_loop().time() - t0

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert elapsed < 1.0, f"response blocked on audit write: {elapsed:.2f}s"
    hang.set()
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_audit_write_timeout_swallowed():
    """Timed-out audit writes must not raise into the request path."""
    app = FastAPI()

    class _TimeoutSessionCM:
        async def __aenter__(self):
            await asyncio.sleep(10)
            return MagicMock()

        async def __aexit__(self, *args):
            return False

    mock_factory = MagicMock(side_effect=lambda: _TimeoutSessionCM())
    app.add_middleware(AuditMiddleware, session_factory=mock_factory)

    @app.post("/api/v1/probe")
    async def probe():
        return {"ok": True}

    with patch(
        "app.modules.audit.middleware._AUDIT_WRITE_TIMEOUT_SECONDS",
        0.05,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/probe", timeout=2.0)

    assert response.status_code == 200
    await asyncio.sleep(0.15)
