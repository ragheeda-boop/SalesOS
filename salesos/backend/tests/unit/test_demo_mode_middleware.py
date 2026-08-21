"""Tests for DemoModeMiddleware — write blocking + contextvar isolation.

Pure ASGI middleware tests — no DB, no external deps.
"""

from __future__ import annotations

import pytest

from app.modules.demo_mode.middleware import (
    DEMO_DB_PREFIX,
    WRITE_METHODS,
    DemoModeMiddleware,
    get_demo_schema,
    demo_schema_ctx,
)


async def _stub_app(scope, receive, send):
    """Minimal ASGI app that sends a 200 OK."""
    from starlette.responses import JSONResponse

    response = JSONResponse(status_code=200, content={"ok": True})
    await response(scope, receive, send)


class TestWriteMethods:
    def test_write_methods_set(self):
        assert WRITE_METHODS == frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def test_get_not_blocked(self):
        assert "GET" not in WRITE_METHODS


class TestDemoPrefix:
    def test_prefix_is_demo_(self):
        assert DEMO_DB_PREFIX == "demo_"


class TestContextVar:
    def test_default_is_none(self):
        token = demo_schema_ctx.set(None)
        try:
            assert get_demo_schema() is None
        finally:
            demo_schema_ctx.reset(token)

    def test_set_returns_prefix(self):
        token = demo_schema_ctx.set(DEMO_DB_PREFIX)
        try:
            assert get_demo_schema() == "demo_"
        finally:
            demo_schema_ctx.reset(token)


class TestDemoModeMiddleware:
    @pytest.mark.asyncio
    async def test_no_demo_header_passthrough(self):
        mw = DemoModeMiddleware(_stub_app)
        scope = {"type": "http", "method": "GET", "path": "/test", "headers": []}
        sent = []

        async def send(msg):
            sent.append(msg)

        await mw(scope, lambda: None, send)
        assert len(sent) >= 1
        assert sent[0]["type"] == "http.response.start"
        assert sent[0]["status"] == 200

    @pytest.mark.asyncio
    async def test_demo_header_blocks_post(self):
        mw = DemoModeMiddleware(_stub_app)
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/companies",
            "headers": [(b"x-demo-mode", b"true")],
        }
        sent = []

        async def send(msg):
            sent.append(msg)

        await mw(scope, lambda: None, send)
        assert sent[0]["status"] == 403

    @pytest.mark.asyncio
    async def test_demo_header_blocks_put(self):
        mw = DemoModeMiddleware(_stub_app)
        scope = {
            "type": "http",
            "method": "PUT",
            "path": "/api/v1/companies/1",
            "headers": [(b"x-demo-mode", b"true")],
        }
        sent = []

        async def send(msg):
            sent.append(msg)

        await mw(scope, lambda: None, send)
        assert sent[0]["status"] == 403

    @pytest.mark.asyncio
    async def test_demo_header_blocks_patch(self):
        mw = DemoModeMiddleware(_stub_app)
        scope = {
            "type": "http",
            "method": "PATCH",
            "path": "/api/v1/companies/1",
            "headers": [(b"x-demo-mode", b"true")],
        }
        sent = []

        async def send(msg):
            sent.append(msg)

        await mw(scope, lambda: None, send)
        assert sent[0]["status"] == 403

    @pytest.mark.asyncio
    async def test_demo_header_blocks_delete(self):
        mw = DemoModeMiddleware(_stub_app)
        scope = {
            "type": "http",
            "method": "DELETE",
            "path": "/api/v1/companies/1",
            "headers": [(b"x-demo-mode", b"true")],
        }
        sent = []

        async def send(msg):
            sent.append(msg)

        await mw(scope, lambda: None, send)
        assert sent[0]["status"] == 403

    @pytest.mark.asyncio
    async def test_demo_header_allows_get(self):
        mw = DemoModeMiddleware(_stub_app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/companies",
            "headers": [(b"x-demo-mode", b"true")],
        }
        sent = []

        async def send(msg):
            sent.append(msg)

        await mw(scope, lambda: None, send)
        assert sent[0]["status"] == 200

    @pytest.mark.asyncio
    async def test_demo_header_adds_response_header(self):
        mw = DemoModeMiddleware(_stub_app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/companies",
            "headers": [(b"x-demo-mode", b"true")],
        }
        sent = []

        async def send(msg):
            sent.append(msg)

        await mw(scope, lambda: None, send)
        resp_start = sent[0]
        headers = dict(resp_start["headers"])
        assert headers[b"x-demo-mode"] == b"true"

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        forwarded = []

        async def lifespan_app(scope, receive, send):
            forwarded.append(scope["type"])

        mw = DemoModeMiddleware(lifespan_app)
        scope = {"type": "lifespan"}
        await mw(scope, lambda: None, lambda msg: None)
        assert forwarded == ["lifespan"]
