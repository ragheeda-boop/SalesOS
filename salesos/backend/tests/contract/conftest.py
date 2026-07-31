"""Fixtures for OpenAPI contract tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.contract.openapi_contract import load_openapi_schema


@pytest.fixture(scope="session")
def openapi_schema() -> dict:
    """FastAPI-generated OpenAPI 3 document (same source as GET /openapi.json)."""
    return load_openapi_schema(app)


@pytest_asyncio.fixture
async def contract_client() -> AsyncClient:
    """ASGI client for public endpoints — no DB override required."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
