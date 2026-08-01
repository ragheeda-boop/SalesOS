"""Fixtures for OpenAPI contract tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from tests.contract.openapi_contract import load_openapi_schema


@pytest.fixture(scope="session")
def openapi_schema() -> dict:
    """FastAPI-generated OpenAPI 3 document (same source as GET /openapi.json)."""
    # Clear cached schema so response_model changes in this process are visible.
    app.openapi_schema = None
    return load_openapi_schema(app)


@pytest_asyncio.fixture
async def contract_client() -> AsyncIterator[AsyncClient]:
    """ASGI client for public no-DB endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@asynccontextmanager
async def _connected_session() -> AsyncIterator[Any]:
    """Honest connected-DB stand-in: execute succeeds (SELECT 1 path)."""
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    yield session


@pytest_asyncio.fixture
async def contract_db_client() -> AsyncIterator[AsyncClient]:
    """ASGI client with get_db + async_session + cache fixtures for /health and /health/ready.

    Does not call real Postgres and does not modify get_db() tenant GUC (DEC-085).
    """
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())

    async def override_get_db():
        yield session

    def fake_async_session():
        return _connected_session()

    cache = AsyncMock()
    cache.health = AsyncMock(return_value=True)

    app.dependency_overrides[get_db] = override_get_db
    previous_cache = getattr(app.state, "cache", None)
    app.state.cache = cache

    transport = ASGITransport(app=app)
    with patch("app.database.async_session", fake_async_session):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.pop(get_db, None)
    if previous_cache is None:
        if hasattr(app.state, "cache"):
            delattr(app.state, "cache")
    else:
        app.state.cache = previous_cache
