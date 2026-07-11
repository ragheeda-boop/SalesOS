"""Tests for per-user rate limiting — sliding window in-memory."""
from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from app.common.rate_limit import _check_rate_limit, _cleanup, rate_limit_dep, _store


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


# ── Tests: _check_rate_limit ─────────────────────────────────────────────────

class TestCheckRateLimit:
    def test_under_limit_returns_none(self):
        retry = _check_rate_limit("test-key", 10, 60)
        assert retry is None

    def test_after_limit_exceeded_returns_retry_after(self):
        key = "burst-key"
        for _ in range(5):
            retry = _check_rate_limit(key, 5, 60)
            assert retry is None
        # The 6th call should exceed
        retry = _check_rate_limit(key, 5, 60)
        assert retry is not None
        assert retry >= 1.0

    def test_different_keys_independent(self):
        for _ in range(5):
            _check_rate_limit("key-a", 5, 60)
        for _ in range(5):
            retry = _check_rate_limit("key-b", 5, 60)
            assert retry is None  # key-b should still be allowed

    def test_limit_of_1(self):
        retry = _check_rate_limit("single-hit", 1, 60)
        assert retry is None
        retry = _check_rate_limit("single-hit", 1, 60)
        assert retry is not None

    def test_window_elapses_allows_new_requests(self):
        key = "window-key"
        with patch("app.common.rate_limit.time") as mock_time:
            mock_time.time.return_value = 1000.0
            for _ in range(3):
                _check_rate_limit(key, 3, 10)
            retry = _check_rate_limit(key, 3, 10)
            assert retry is not None

            # Advance past the window
            mock_time.time.return_value = 1011.0
            retry = _check_rate_limit(key, 3, 10)
            assert retry is None


# ── Tests: _cleanup ──────────────────────────────────────────────────────────

class TestCleanup:
    def test_removes_expired_entries(self):
        key = "expired-entry"
        with patch("app.common.rate_limit.time") as mock_time:
            mock_time.time.return_value = 1000.0
            _check_rate_limit(key, 10, 60)
            assert key in _store

            mock_time.time.return_value = 5000.0  # > 1 hour later
            _cleanup(mock_time.time.return_value)
            assert key not in _store

    def test_keeps_recent_entries(self):
        key = "recent-entry"
        with patch("app.common.rate_limit.time") as mock_time:
            mock_time.time.return_value = 1000.0
            _check_rate_limit(key, 10, 60)
            _cleanup(2000.0)  # 1000 seconds later, within 1 hour
            assert key in _store

    def test_cleanup_removes_empty_keys(self):
        _store["stale-key"] = []
        _cleanup(time.time())
        assert "stale-key" not in _store


# ── Tests: rate_limit_dep ────────────────────────────────────────────────────

class TestRateLimitDep:
    @pytest.fixture
    def mock_request(self):
        req = MagicMock(spec=Request)
        req.state.user_id = "user-123"
        return req

    async def test_returns_none_when_under_limit(self, mock_request):
        dep = rate_limit_dep("test-resource", 10, 60)
        result = await dep(request=mock_request, tenant_id="tenant-1")
        assert result is None

    async def test_raises_429_when_exceeded(self, mock_request):
        dep = rate_limit_dep("burst-resource", 3, 60)
        for _ in range(3):
            await dep(request=mock_request, tenant_id="tenant-1")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request=mock_request, tenant_id="tenant-1")
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail

    async def test_anonymous_user_when_no_user_id(self, mock_request):
        mock_request.state.user_id = None
        dep = rate_limit_dep("anon-test", 1, 60)
        await dep(request=mock_request, tenant_id="t-1")
        with pytest.raises(HTTPException):
            await dep(request=mock_request, tenant_id="t-1")

    async def test_different_tenants_separate_limits(self, mock_request):
        dep = rate_limit_dep("multi-tenant", 2, 60)
        await dep(request=mock_request, tenant_id="t-1")
        await dep(request=mock_request, tenant_id="t-1")
        # t-2 should still be allowed
        result = await dep(request=mock_request, tenant_id="t-2")
        assert result is None

    async def test_retry_after_header_in_exception(self, mock_request):
        dep = rate_limit_dep("header-test", 1, 60)
        await dep(request=mock_request, tenant_id="t-1")
        with pytest.raises(HTTPException) as exc_info:
            await dep(request=mock_request, tenant_id="t-1")
        headers = exc_info.value.headers
        assert headers is not None
        assert "Retry-After" in headers
        assert int(headers["Retry-After"]) >= 1
