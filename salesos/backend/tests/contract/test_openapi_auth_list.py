"""OpenAPI HTTP contract for one authenticated list endpoint (DEC-094 slice 3).

GET /api/v1/decisions — DecisionListResponse (typed items + cursor fields).
Uses honest verify_token override + in-memory Decision Center; no fake OpenAPI
schemas; no get_db tenant GUC edits (DEC-085).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app
from tests.contract.conftest import CONTRACT_TENANT_ID
from tests.contract.openapi_contract import assert_response_matches_openapi


@pytest.mark.contract
@pytest.mark.asyncio
async def test_decisions_list_response_matches_openapi(
    contract_auth_client: AsyncClient,
    openapi_schema: dict,
) -> None:
    path = "/api/v1/decisions"
    svc = app.state.decision_center_service
    await svc.create_decision(
        domain="pipeline",
        decision_type="deal_scoring",
        entity_id="co-contract-1",
        entity_type="company",
        decision="pursue",
        confidence=0.85,
        reasoning="Contract-test seed",
        provider="rule_engine",
        tenant_id=CONTRACT_TENANT_ID,
    )

    response = await contract_auth_client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert_response_matches_openapi(
        openapi_schema,
        path=path,
        method="get",
        status_code=200,
        body=body,
    )
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 1
    assert body["total"] == 1
    assert body["limit"] == 50
    assert body["has_next"] is False
    assert body.get("next_cursor") is None
    item = body["items"][0]
    assert item["entityId"] == "co-contract-1"
    assert item["type"] == "deal_scoring"
    assert item["decision"] == "pursue"


@pytest.mark.contract
def test_decisions_list_schema_in_openapi(openapi_schema: dict) -> None:
    path = "/api/v1/decisions"
    assert path in openapi_schema["paths"], f"missing OpenAPI path: {path}"
    get_op = openapi_schema["paths"][path]["get"]
    schema = get_op["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema.get("$ref") == "#/components/schemas/DecisionListResponse"
    components = openapi_schema["components"]["schemas"]
    assert "DecisionListResponse" in components
    assert "DecisionResponse" in components
    items = components["DecisionListResponse"]["properties"]["items"]
    assert items["type"] == "array"
    assert items["items"].get("$ref") == "#/components/schemas/DecisionResponse"
    props = components["DecisionListResponse"]["properties"]
    assert "next_cursor" in props
    assert "has_next" in props
