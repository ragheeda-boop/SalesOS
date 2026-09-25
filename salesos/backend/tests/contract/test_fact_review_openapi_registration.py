"""OpenAPI registration contract for the authenticated Fact Review API."""

import pytest


@pytest.mark.contract
def test_fact_review_routes_are_mounted_in_openapi(openapi_schema: dict) -> None:
    expected_operations = {
        "/api/v1/facts/proposals": {"get", "post"},
        "/api/v1/facts/proposals/from-agent-reach": {"post"},
        "/api/v1/facts/{fact_id}/decision": {"post"},
    }

    for path, methods in expected_operations.items():
        assert path in openapi_schema["paths"], f"missing OpenAPI path: {path}"
        for method in methods:
            assert method in openapi_schema["paths"][path], f"missing {method.upper()} {path}"
