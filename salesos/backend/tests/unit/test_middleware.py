"""Unit tests for middleware: CSRF, SecurityHeaders, RequestID, RateLimit (ASGI level)."""

from __future__ import annotations

import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.middleware import (
    BodyCacheMiddleware,
    CsrfEnforcementMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    _get_client_ip,
)


async def _dummy_app(scope, receive, send):
    """Minimal ASGI app that sends a 200 OK."""
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body"})


async def _collecting_app(collected, scope, receive, send):
    collected.append(scope)
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body"})


def _make_scope(
    path="/",
    method="GET",
    headers=None,
    client=("127.0.0.1", 12345),
):
    h = []
    for k, v in (headers or {}).items():
        h.append((k.encode() if isinstance(k, str) else k,
                  v.encode() if isinstance(v, str) else v))
    return {
        "type": "http",
        "path": path,
        "method": method,
        "headers": h,
        "client": client,
    }


# ── _get_client_ip ────────────────────────────────────────────────────────

class TestGetClientIp:
    def test_direct_client(self):
        scope = {"client": ("1.2.3.4", 80)}
        assert _get_client_ip(scope) == "1.2.3.4"

    def test_x_forwarded_for(self):
        scope = {
            "headers": [(b"x-forwarded-for", b"10.0.0.1, 10.0.0.2")],
        }
        assert _get_client_ip(scope) == "10.0.0.1"

    def test_x_real_ip(self):
        scope = {
            "headers": [(b"x-real-ip", b"5.6.7.8")],
        }
        assert _get_client_ip(scope) == "5.6.7.8"

    def test_no_client_no_headers(self):
        assert _get_client_ip({}) == "unknown"

    def test_empty_x_forwarded_for(self):
        scope = {
            "headers": [(b"x-forwarded-for", b"")],
            "client": ("1.1.1.1", 80),
        }
        assert _get_client_ip(scope) == "1.1.1.1"


# ── BodyCacheMiddleware ──────────────────────────────────────────────────

class TestBodyCacheMiddleware:
    @pytest.mark.asyncio
    async def test_caches_body_in_scope(self):
        """Body should be stored in scope['body_cache'] after middleware."""
        captured_scope = {}

        async def inner_app(scope, receive, send):
            captured_scope.update(scope)
            msg = await receive()
            assert msg["type"] == "http.request"
            assert msg["more_body"] is False
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body"})

        app = BodyCacheMiddleware(inner_app)
        scope = _make_scope(method="POST")

        async def receive():
            return {"type": "http.request", "body": b"hello world", "more_body": False}

        await app(scope, receive, AsyncMock())
        assert scope["body_cache"] == b"hello world"
        assert captured_scope["body_cache"] == b"hello world"

    @pytest.mark.asyncio
    async def test_handles_chunked_body(self):
        """Multiple chunks should be assembled into one body via cached_receive."""
        received_messages = []

        async def inner_app(scope, receive, send):
            msg1 = await receive()
            msg2 = await receive()
            received_messages.append(msg1)
            received_messages.append(msg2)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body"})

        app = BodyCacheMiddleware(inner_app)
        scope = _make_scope(method="POST")
        chunks = [
            {"type": "http.request", "body": b"chunk1", "more_body": True},
            {"type": "http.request", "body": b"chunk2", "more_body": False},
        ]
        chunk_idx = [0]

        async def receive():
            idx = chunk_idx[0]
            chunk_idx[0] += 1
            return chunks[idx]

        await app(scope, receive, AsyncMock())
        # cached_receive assembles chunks and returns full body on first call
        assert received_messages[0]["body"] == b"chunk1chunk2"
        assert received_messages[0]["more_body"] is False
        # Second call returns disconnect
        assert received_messages[1]["type"] == "http.disconnect"

    @pytest.mark.asyncio
    async def test_cached_receive_returns_disconnect_after_first_call(self):
        """Second call to cached_receive should return http.disconnect."""
        received_messages = []

        async def inner_app(scope, receive, send):
            msg1 = await receive()
            msg2 = await receive()
            received_messages.append(msg1)
            received_messages.append(msg2)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body"})

        app = BodyCacheMiddleware(inner_app)
        scope = _make_scope(method="POST")

        async def receive():
            return {"type": "http.request", "body": b"test", "more_body": False}

        await app(scope, receive, AsyncMock())
        assert received_messages[0]["type"] == "http.request"
        assert received_messages[0]["body"] == b"test"
        assert received_messages[1]["type"] == "http.disconnect"

    @pytest.mark.asyncio
    async def test_oversized_body_returns_413(self):
        """Body exceeding max_body_size should return 413."""
        app = BodyCacheMiddleware(_dummy_app, max_body_size=100)
        scope = _make_scope(method="POST")
        large_body = b"x" * 200

        async def receive():
            return {"type": "http.request", "body": large_body, "more_body": False}

        responses = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                responses.append(msg["status"])

        await app(scope, receive, send)
        assert responses[0] == 413
        assert scope.get("body_cache") is None  # body should NOT be cached

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        """Non-HTTP scopes should pass through without body reading."""
        collected = []
        app = BodyCacheMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send)
        )
        await app({"type": "websocket"}, AsyncMock(), AsyncMock())
        assert len(collected) == 1

    @pytest.mark.asyncio
    async def test_empty_body(self):
        """POST with empty body should work."""
        async def inner_app(scope, receive, send):
            msg = await receive()
            assert msg["body"] == b""
            assert scope["body_cache"] == b""
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body"})

        app = BodyCacheMiddleware(inner_app)
        scope = _make_scope(method="POST")

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        await app(scope, receive, AsyncMock())
        assert scope["body_cache"] == b""


# ── CsrfEnforcementMiddleware ────────────────────────────────────────────

class TestCsrfMiddleware:
    @pytest.fixture(autouse=True)
    def _testing_mode_off(self):
        os.environ.pop("SALESOS_TESTING", None)
        yield
        os.environ["SALESOS_TESTING"] = "true"

    @pytest.mark.asyncio
    async def test_get_skips_csrf(self):
        collected = []
        app = CsrfEnforcementMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send)
        )
        scope = _make_scope(method="GET")
        await app(scope, AsyncMock(), AsyncMock())
        assert len(collected) == 1

    @pytest.mark.asyncio
    async def test_post_without_token_returns_403(self):
        responses = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                responses.append(msg["status"])

        app = CsrfEnforcementMiddleware(_dummy_app)
        scope = _make_scope(method="POST", headers={})
        await app(scope, AsyncMock(), send)
        assert responses[0] == 403

    @pytest.mark.asyncio
    async def test_post_with_matching_csrf_passes(self):
        collected = []
        app = CsrfEnforcementMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send)
        )
        scope = _make_scope(
            method="POST",
            headers={
                "cookie": "csrf_token=abc123",
                "x-csrf-token": "abc123",
            },
        )
        await app(scope, AsyncMock(), AsyncMock())
        assert len(collected) == 1

    @pytest.mark.asyncio
    async def test_post_with_mismatched_csrf_returns_403(self):
        responses = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                responses.append(msg["status"])

        app = CsrfEnforcementMiddleware(_dummy_app)
        scope = _make_scope(
            method="POST",
            headers={
                "cookie": "csrf_token=abc123",
                "x-csrf-token": "WRONG",
            },
        )
        await app(scope, AsyncMock(), send)
        assert responses[0] == 403

    @pytest.mark.asyncio
    async def test_post_with_unverified_api_key_still_requires_csrf(self):
        """PROD-W5-001: non-empty X-API-Key alone must not skip CSRF."""
        responses = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                responses.append(msg["status"])

        app = CsrfEnforcementMiddleware(_dummy_app)
        scope = _make_scope(
            method="POST",
            headers={"x-api-key": "sos_fake_unverified"},
        )
        await app(scope, AsyncMock(), send)
        assert responses[0] == 403

    @pytest.mark.asyncio
    async def test_post_with_authenticated_api_key_requires_csrf(self):
        """API-key auth alone must NOT bypass CSRF (PROD-W5-001 fix)."""
        responses = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                responses.append(msg["status"])

        app = CsrfEnforcementMiddleware(_dummy_app)
        scope = _make_scope(
            method="POST",
            headers={"x-api-key": "sos_valid"},
        )
        scope["state"] = {"api_key_authenticated": True}
        await app(scope, AsyncMock(), send)
        assert responses[0] == 403

    @pytest.mark.asyncio
    async def test_public_path_skips_csrf(self):
        collected = []
        app = CsrfEnforcementMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send)
        )
        scope = _make_scope(method="POST", path="/api/v1/identity/login")
        await app(scope, AsyncMock(), AsyncMock())
        assert len(collected) == 1

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        collected = []
        app = CsrfEnforcementMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send)
        )
        await app({"type": "websocket"}, AsyncMock(), AsyncMock())
        assert len(collected) == 1


# ── SecurityHeadersMiddleware ────────────────────────────────────────────

class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_adds_security_headers(self):
        headers_added = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                headers_added.extend(msg.get("headers", []))

        app = SecurityHeadersMiddleware(_dummy_app)
        scope = _make_scope(path="/api/v1/companies")
        await app(scope, AsyncMock(), send)
        header_names = [h[0] for h in headers_added]
        assert b"content-security-policy" in header_names
        assert b"x-content-type-options" in header_names
        assert b"x-frame-options" in header_names
        assert b"strict-transport-security" in header_names

    @pytest.mark.asyncio
    async def test_docs_route_uses_relaxed_csp(self):
        csp_values = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                for h in msg.get("headers", []):
                    if h[0] == b"content-security-policy":
                        csp_values.append(h[1])

        app = SecurityHeadersMiddleware(_dummy_app)
        scope = _make_scope(path="/docs")
        await app(scope, AsyncMock(), send)
        assert len(csp_values) == 1
        assert b"cdn.jsdelivr.net" in csp_values[0]

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        collected = []
        app = SecurityHeadersMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send)
        )
        await app({"type": "websocket"}, AsyncMock(), AsyncMock())
        assert len(collected) == 1


# ── RequestIDMiddleware ──────────────────────────────────────────────────

class TestRequestIDMiddleware:
    @pytest.mark.asyncio
    async def test_generates_request_id_if_missing(self):
        scope_ids = []
        header_ids = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                for h in msg.get("headers", []):
                    if h[0] == b"x-request-id":
                        header_ids.append(h[1].decode())

        async def inner_app(scope, receive, send):
            scope_ids.append(scope.get("request_id", ""))
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body"})

        app = RequestIDMiddleware(inner_app)
        scope = _make_scope()
        await app(scope, AsyncMock(), send)
        assert len(scope_ids) == 1
        assert len(header_ids) == 1
        assert scope_ids[0] != ""
        assert scope_ids[0] == header_ids[0]

    @pytest.mark.asyncio
    async def test_uses_existing_request_id(self):
        scope_ids = []
        header_ids = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                for h in msg.get("headers", []):
                    if h[0] == b"x-request-id":
                        header_ids.append(h[1].decode())

        async def inner_app(scope, receive, send):
            scope_ids.append(scope.get("request_id", ""))
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body"})

        app = RequestIDMiddleware(inner_app)
        scope = _make_scope(headers={"x-request-id": "my-custom-id"})
        await app(scope, AsyncMock(), send)
        assert all(rid == "my-custom-id" for rid in scope_ids + header_ids)

    @pytest.mark.asyncio
    async def test_adds_response_time_header(self):
        response_headers = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                response_headers.extend(msg.get("headers", []))

        app = RequestIDMiddleware(_dummy_app)
        scope = _make_scope()
        await app(scope, AsyncMock(), send)
        header_names = [h[0] for h in response_headers]
        assert b"x-response-time" in header_names

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        collected = []
        app = RequestIDMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send)
        )
        await app({"type": "websocket"}, AsyncMock(), AsyncMock())
        assert len(collected) == 1


# ── RateLimitMiddleware ──────────────────────────────────────────────────

class TestRateLimitMiddleware:
    @pytest.fixture(autouse=True)
    def _testing_mode_off(self):
        os.environ.pop("SALESOS_TESTING", None)
        yield
        os.environ["SALESOS_TESTING"] = "true"

    @pytest.mark.asyncio
    async def test_allows_under_limit(self):
        collected = []
        app = RateLimitMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send),
            window=60,
        )
        scope = _make_scope(path="/api/v1/companies")
        await app(scope, AsyncMock(), AsyncMock())
        assert len(collected) == 1

    @pytest.mark.asyncio
    async def test_rate_limit_headers_on_429(self):
        responses = []
        status_codes = []

        async def send(msg):
            if msg["type"] == "http.response.start":
                status_codes.append(msg["status"])
                responses.append(msg)

        app = RateLimitMiddleware(_dummy_app, window=60)
        # Override the tier to a low value for testing
        with patch.object(app, "_select_tier", return_value=2):
            for _ in range(3):
                status_codes.clear()
                await app(_make_scope(), AsyncMock(), send)
            # The 3rd request should be rate-limited
            assert 429 in status_codes

    @pytest.mark.asyncio
    async def test_different_ips_independent(self):
        collected_a = []
        collected_b = []
        counter = {"count": 0}

        async def counting_app(scope, receive, send):
            counter["count"] += 1
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body"})

        app = RateLimitMiddleware(counting_app, window=60)
        with patch.object(app, "_select_tier", return_value=2):
            await app(_make_scope(client=("1.1.1.1", 1)), AsyncMock(), AsyncMock())
            await app(_make_scope(client=("1.1.1.1", 2)), AsyncMock(), AsyncMock())
            await app(_make_scope(client=("2.2.2.2", 3)), AsyncMock(), AsyncMock())
            assert counter["count"] == 3

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        collected = []
        app = RateLimitMiddleware(
            lambda s, r, send: _collecting_app(collected, s, r, send),
            window=60,
        )
        await app({"type": "websocket"}, AsyncMock(), AsyncMock())
        assert len(collected) == 1

    @pytest.mark.asyncio
    async def test_cleanup_removes_stale_entries(self):
        app = RateLimitMiddleware(_dummy_app, window=60)
        app._local["ratelimit:1.2.3.4"] = [time.time() - 7200]
        app._last_cleanup = 0
        app._cleanup_local(time.time())
        assert "ratelimit:1.2.3.4" not in app._local
