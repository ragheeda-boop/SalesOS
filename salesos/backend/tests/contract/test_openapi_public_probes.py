"""OpenAPI HTTP contracts for public probes (DEC-094 slice 1).

Extends STORY-03-04 (`test_openapi_contract.py` csrf seed) with typed
no-DB endpoints. Slice 2 (/health+/health/ready) lives in
`test_openapi_health_ready.py`.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.contract.openapi_contract import assert_response_matches_openapi


@pytest.mark.contract
@pytest.mark.asyncio
async def test_ping_response_matches_openapi(
    contract_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    path = "/ping"
    response = await contract_client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert_response_matches_openapi(
        openapi_schema,
        path=path,
        method="get",
        status_code=200,
        body=body,
    )
    assert body == {"ping": "pong"}


@pytest.mark.contract
@pytest.mark.asyncio
async def test_health_live_response_matches_openapi(
    contract_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    path = "/health/live"
    response = await contract_client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert_response_matches_openapi(
        openapi_schema,
        path=path,
        method="get",
        status_code=200,
        body=body,
    )
    assert body.get("status") == "alive"
    assert isinstance(body.get("uptime_seconds"), int | float)
    assert body["uptime_seconds"] >= 0


@pytest.mark.contract
def test_public_probe_schemas_in_openapi(openapi_schema: dict) -> None:
    for path in ("/ping", "/health/live", "/api/v1/identity/csrf-token"):
        assert path in openapi_schema["paths"], f"missing OpenAPI path: {path}"
    components = openapi_schema["components"]["schemas"]
    assert "PingResponse" in components
    assert "HealthLiveResponse" in components
