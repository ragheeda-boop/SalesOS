"""OpenAPI contract test helpers (TEST_STRATEGY.md §3).

Validates live HTTP responses against the FastAPI-generated OpenAPI document.
Uses stdlib + existing ``jsonschema`` dependency — no Schemathesis required.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def load_openapi_schema(app) -> dict[str, Any]:
    """Return the canonical OpenAPI 3 document from the FastAPI app."""
    schema = app.openapi()
    if not isinstance(schema, dict):
        raise TypeError("app.openapi() must return a dict")
    if not schema.get("openapi", "").startswith("3."):
        raise ValueError(f"Expected OpenAPI 3.x document, got: {schema.get('openapi')!r}")
    return schema


def _resolve_ref(node: Any, root: dict[str, Any], seen: frozenset[str]) -> Any:
    if not isinstance(node, dict):
        return node

    ref = node.get("$ref")
    if ref is None:
        resolved = {key: _resolve_ref(value, root, seen) for key, value in node.items()}
        return resolved

    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise ValueError(f"Unsupported $ref (expected local fragment): {ref!r}")
    if ref in seen:
        return node

    target: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(target, dict) or part not in target:
            raise KeyError(f"Could not resolve $ref {ref!r}")
        target = target[part]

    return _resolve_ref(deepcopy(target), root, seen | {ref})


def get_response_schema(
    openapi: dict[str, Any],
    *,
    path: str,
    method: str,
    status_code: int = 200,
    content_type: str = "application/json",
) -> dict[str, Any]:
    """Resolve the response body schema for an operation."""
    method = method.lower()
    try:
        operation = openapi["paths"][path][method]
    except KeyError as exc:
        raise KeyError(
            f"Operation {method.upper()} {path} not found in OpenAPI paths"
        ) from exc

    responses = operation.get("responses", {})
    response = responses.get(str(status_code)) or responses.get("default")
    if response is None:
        available = ", ".join(sorted(responses))
        raise KeyError(
            f"No {status_code} (or default) response for {method.upper()} {path}; "
            f"available: {available or 'none'}"
        )

    content = response.get("content", {})
    media = content.get(content_type)
    if media is None:
        available = ", ".join(sorted(content))
        raise KeyError(
            f"No {content_type!r} content for {status_code} on {method.upper()} {path}; "
            f"available: {available or 'none'}"
        )

    schema = media.get("schema")
    if schema is None:
        raise KeyError(
            f"No JSON schema declared for {status_code} {method.upper()} {path}"
        )

    return _resolve_ref(schema, openapi, frozenset())


def validate_json_against_schema(instance: Any, schema: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError when *instance* does not match *schema*."""
    Draft202012Validator(schema).validate(instance)


def assert_response_matches_openapi(
    openapi: dict[str, Any],
    *,
    path: str,
    method: str,
    status_code: int,
    body: Any,
    content_type: str = "application/json",
) -> None:
    """Assert an HTTP JSON body conforms to the documented OpenAPI response schema."""
    schema = get_response_schema(
        openapi,
        path=path,
        method=method,
        status_code=status_code,
        content_type=content_type,
    )
    try:
        validate_json_against_schema(body, schema)
    except ValidationError as exc:
        raise AssertionError(
            f"{method.upper()} {path} response failed OpenAPI contract: {exc.message}"
        ) from exc
