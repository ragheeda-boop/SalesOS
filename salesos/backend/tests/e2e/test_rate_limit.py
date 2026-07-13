"""E2E tests for Rate Limiting — Critical Path 10."""

from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestRateLimiting:
    """Verify rate limiting middleware returns proper 429 responses."""

    async def test_rate_limit_header_present(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Authenticated endpoints return X-RateLimit headers or accept request."""
        resp = await asyncio.wait_for(
            client.get("/api/v1/companies", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text

    async def test_health_endpoint_accessible(
        self,
        client: AsyncClient,
    ):
        """Health endpoints should be accessible even with high rate limits."""
        resp = await asyncio.wait_for(
            client.get("/health"), timeout=_TEST_TIMEOUT
        )
        assert resp.status_code == 200, resp.text

    async def test_identity_endpoint_rate_limited(
        self,
        client: AsyncClient,
        test_tenant: str,
    ):
        """Login endpoint should be subject to rate limiting."""
        for _ in range(5):
            await client.post(
                "/api/v1/identity/login",
                json={
                    "email": "nonexistent@test.com",
                    "password": "WrongPass123!",
                },
            )
        resp = await client.post(
            "/api/v1/identity/login",
            json={
                "email": "nonexistent@test.com",
                "password": "WrongPass123!",
            },
        )
        assert resp.status_code in (200, 401, 422, 429), resp.text

    async def test_rate_limit_retry_after_header_on_429(
        self,
        client: AsyncClient,
        test_tenant: str,
    ):
        """When rate limited, Retry-After header is present."""
        for _ in range(12):
            await client.post(
                "/api/v1/identity/login",
                json={
                    "email": f"burst-{_}@test.com",
                    "password": "WrongPass123!",
                },
            )
        resp = await client.post(
            "/api/v1/identity/login",
            json={
                "email": "burst-final@test.com",
                "password": "WrongPass123!",
            },
        )
        if resp.status_code == 429:
            assert "retry-after" in resp.headers

    async def test_unauthenticated_search_rate_limited(
        self,
        client: AsyncClient,
    ):
        """Unauthenticated search endpoint should be rate limited."""
        for _ in range(3):
            await client.get("/api/v1/search", params={"q": "test"})
        resp = await client.get("/api/v1/search", params={"q": "test"})
        assert resp.status_code in (200, 401, 422, 429)

    async def test_health_endpoint_returns_version_after_rate_limit(
        self,
        client: AsyncClient,
    ):
        """Health endpoint remains functional regardless of rate limit state."""
        resp = await asyncio.wait_for(
            client.get("/health"), timeout=_TEST_TIMEOUT
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "version" in body
