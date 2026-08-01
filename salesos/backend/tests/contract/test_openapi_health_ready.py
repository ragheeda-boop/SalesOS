"""OpenAPI HTTP contracts for /health and /health/ready (DEC-094 slice 2).

Uses honest get_db / async_session / cache fixtures — no real Postgres,
and no edits to get_db tenant GUC (DEC-085 set_config).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings
from tests.contract.openapi_contract import assert_response_matches_openapi


@pytest.mark.contract
@pytest.mark.asyncio
async def test_health_response_matches_openapi(
    contract_db_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    path = "/health"
    response = await contract_db_client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert_response_matches_openapi(
        openapi_schema,
        path=path,
        method="get",
        status_code=200,
        body=body,
    )
    assert body["status"] == "ok"
    assert body["version"] == settings.service_version
    assert body["database"] == "connected"
    assert body["cache"] == "connected"
    assert isinstance(body["uptime_seconds"], (int, float))
    assert body["uptime_seconds"] >= 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_health_ready_response_matches_openapi(
    contract_db_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    path = "/health/ready"
    response = await contract_db_client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert_response_matches_openapi(
        openapi_schema,
        path=path,
        method="get",
        status_code=200,
        body=body,
    )
    assert body["status"] == "ready"
    assert isinstance(body["checks"], dict)
    assert body["checks"]["database"] == "connected"
    assert body["checks"]["cache"] == "connected"


@pytest.mark.contract
def test_health_ready_schemas_in_openapi(openapi_schema: dict) -> None:
    for path in ("/health", "/health/ready"):
        assert path in openapi_schema["paths"], f"missing OpenAPI path: {path}"
    components = openapi_schema["components"]["schemas"]
    assert "HealthResponse" in components
    assert "HealthReadyResponse" in components
