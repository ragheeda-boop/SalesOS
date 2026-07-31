"""OpenAPI / HTTP contract tests (TEST_STRATEGY.md §3).

These tests exercise real endpoints and validate responses against the
documented OpenAPI schema — not Pydantic model unit tests.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.contract.openapi_contract import assert_response_matches_openapi, load_openapi_schema


@pytest.mark.contract
def test_openapi_document_is_valid(openapi_schema: dict) -> None:
    """Smoke: generated schema is OpenAPI 3.x with expected metadata."""
    assert openapi_schema["openapi"].startswith("3.")
    assert openapi_schema["info"]["title"] == "SalesOS API"
    assert "/api/v1/identity/csrf-token" in openapi_schema["paths"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_csrf_token_response_matches_openapi(
    contract_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    """GET /api/v1/identity/csrf-token — first real endpoint contract test."""
    path = "/api/v1/identity/csrf-token"
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
    assert isinstance(body.get("csrf_token"), str)
    assert body["csrf_token"]


@pytest.mark.contract
def test_openapi_schema_loads_from_app() -> None:
    """Document the schema generation path: FastAPI app.openapi()."""
    from app.main import app

    schema = load_openapi_schema(app)
    assert "components" in schema
    assert "schemas" in schema["components"]
