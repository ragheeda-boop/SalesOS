"""OpenAPI HTTP contracts for auth/validation errors (DEC-094 slice 4).

GET /api/v1/decisions — 401 (UnauthorizedError string detail) + 422 (HTTPValidationError).
Does not invent ErrorResponse; uses documented FastAPI shapes. No get_db GUC edits (DEC-085).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.contract.openapi_contract import assert_response_matches_openapi

PATH = "/api/v1/decisions"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_decisions_list_401_matches_openapi(
    contract_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    """Missing Authorization → 401 {"detail": str} per DetailStringError."""
    response = await contract_client.get(PATH)
    assert response.status_code == 401
    body = response.json()
    assert_response_matches_openapi(
        openapi_schema,
        path=PATH,
        method="get",
        status_code=401,
        body=body,
    )
    assert isinstance(body.get("detail"), str)
    assert body["detail"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_decisions_list_422_matches_openapi(
    contract_auth_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    """Auth OK + limit out of range → 422 HTTPValidationError."""
    response = await contract_auth_client.get(PATH, params={"limit": 0})
    assert response.status_code == 422
    body = response.json()
    assert_response_matches_openapi(
        openapi_schema,
        path=PATH,
        method="get",
        status_code=422,
        body=body,
    )
    assert isinstance(body.get("detail"), list)
    assert len(body["detail"]) >= 1


@pytest.mark.contract
def test_decisions_list_error_schemas_in_openapi(openapi_schema: dict) -> None:
    """OpenAPI documents 401 DetailStringError and 422 HTTPValidationError."""
    assert PATH in openapi_schema["paths"], f"missing OpenAPI path: {PATH}"
    responses = openapi_schema["paths"][PATH]["get"]["responses"]
    assert "401" in responses
    assert "422" in responses

    schema_401 = responses["401"]["content"]["application/json"]["schema"]
    assert schema_401.get("$ref") == "#/components/schemas/DetailStringError"
    components = openapi_schema["components"]["schemas"]
    assert "DetailStringError" in components
    assert components["DetailStringError"]["properties"]["detail"]["type"] == "string"

    schema_422 = responses["422"]["content"]["application/json"]["schema"]
    assert schema_422.get("$ref") == "#/components/schemas/HTTPValidationError"
    assert "HTTPValidationError" in components
    assert "ValidationError" in components
