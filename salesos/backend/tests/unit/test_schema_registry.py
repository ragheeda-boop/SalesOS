"""Tests for JSON Schema registry for event validation."""

from sdk.events.base import DomainEvent
from sdk.events.schema_registry import (
    validate_event,
    get_schema,
    register_schema,
    export_schemas,
)


def test_get_schema_registered() -> None:
    schema = get_schema("company.created")
    assert schema is not None
    assert schema["title"] == "CompanyCreated"
    assert "company_id" in {p["title"] if isinstance(p, dict) and "title" in p else p for p in schema.get("properties", {})}


def test_get_schema_unregistered() -> None:
    assert get_schema("nonexistent.event") is None


def test_validate_valid_event() -> None:
    event = DomainEvent(
        event_type="company.created",
        data={"company_id": "c-1", "name": "Acme", "tenant_id": "t-1"},
    )
    errors = validate_event(event)
    assert errors == []


def test_validate_missing_required_field() -> None:
    event = DomainEvent(
        event_type="company.created",
        data={"name": "Acme"},  # missing company_id, tenant_id
    )
    errors = validate_event(event)
    assert len(errors) > 0
    assert any("company_id" in e for e in errors)


def test_validate_unregistered_event_skips() -> None:
    event = DomainEvent(event_type="unknown.event", data={})
    errors = validate_event(event)
    assert errors == []


def test_validate_opportunity_created() -> None:
    event = DomainEvent(
        event_type="opportunity.created",
        data={
            "opportunity_id": "opp-1",
            "company_id": "c-1",
            "tenant_id": "t-1",
            "name": "Big Deal",
            "value": 100000,
            "stage": "qualification",
        },
    )
    errors = validate_event(event)
    assert errors == []


def test_validate_opportunity_won() -> None:
    event = DomainEvent(
        event_type="opportunity.won",
        data={"opportunity_id": "opp-1", "tenant_id": "t-1", "value": 50000, "close_date": "2026-08-01"},
    )
    errors = validate_event(event)
    assert errors == []


def test_validate_company_merged() -> None:
    event = DomainEvent(
        event_type="company.merged",
        data={"survivor_id": "c-1", "merged_ids": ["c-2", "c-3"], "tenant_id": "t-1"},
    )
    errors = validate_event(event)
    assert errors == []


def test_validate_wrong_type_for_field() -> None:
    event = DomainEvent(
        event_type="company.created",
        data={"company_id": "c-1", "name": "Acme", "tenant_id": 123},  # tenant_id should be string
    )
    errors = validate_event(event)
    assert len(errors) > 0
    assert any("type 'string'" in e for e in errors)


def test_register_new_schema() -> None:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "TestEvent",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
    }
    register_schema("test.event", schema)

    fetched = get_schema("test.event")
    assert fetched is not None
    assert fetched["title"] == "TestEvent"

    # Validate
    valid = DomainEvent(event_type="test.event", data={"value": 42})
    assert validate_event(valid) == []

    invalid = DomainEvent(event_type="test.event", data={"value": "not-a-number"})
    errors = validate_event(invalid)
    assert len(errors) > 0


def test_export_schemas_contains_registered() -> None:
    schemas = export_schemas()
    assert "company.created" in schemas
    assert "opportunity.created" in schemas
    assert "user.registered" in schemas
    assert "entity_resolution.completed" in schemas
