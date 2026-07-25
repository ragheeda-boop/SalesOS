"""JSON Schema registry for domain event validation.

Every event type registered in this module has a corresponding JSON Schema
that is used to validate both produced and consumed events.

Schemas are defined in Python dicts for portability. They can be exported
to a Confluent Schema Registry or any JSON Schema store.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sdk.events.base import DomainEvent

logger = logging.getLogger(__name__)

# ── Schema definitions ──────────────────────────────────────────────────────

EVENT_SCHEMAS: dict[str, dict[str, Any]] = {}

# ── Identity ────────────────────────────────────────────────────────────────

EVENT_SCHEMAS["tenant.created"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "TenantCreated",
    "properties": {
        "tenant_id": {"type": "string", "description": "Unique tenant identifier"},
        "name": {"type": "string"},
        "domain": {"type": "string"},
        "plan": {"type": "string", "enum": ["free", "starter", "professional", "enterprise"]},
    },
    "required": ["tenant_id", "name"],
}

EVENT_SCHEMAS["user.registered"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "UserRegistered",
    "properties": {
        "user_id": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "tenant_id": {"type": "string"},
        "role": {"type": "string"},
    },
    "required": ["user_id", "email", "tenant_id"],
}

EVENT_SCHEMAS["user.role_changed"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "UserRoleChanged",
    "properties": {
        "user_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "old_role": {"type": "string"},
        "new_role": {"type": "string"},
    },
    "required": ["user_id", "tenant_id", "new_role"],
}

# ── Company ─────────────────────────────────────────────────────────────────

EVENT_SCHEMAS["company.created"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "CompanyCreated",
    "properties": {
        "company_id": {"type": "string"},
        "name": {"type": "string"},
        "domain": {"type": "string"},
        "tenant_id": {"type": "string"},
        "source": {"type": "string"},
    },
    "required": ["company_id", "name", "tenant_id"],
}

EVENT_SCHEMAS["company.merged"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "CompanyMerged",
    "properties": {
        "survivor_id": {"type": "string"},
        "merged_ids": {"type": "array", "items": {"type": "string"}},
        "tenant_id": {"type": "string"},
    },
    "required": ["survivor_id", "merged_ids", "tenant_id"],
}

EVENT_SCHEMAS["company.enriched"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "CompanyEnriched",
    "properties": {
        "company_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "enriched_fields": {"type": "array", "items": {"type": "string"}},
        "enrichment_source": {"type": "string"},
    },
    "required": ["company_id", "tenant_id"],
}

# ── Entity Resolution ──────────────────────────────────────────────────────

EVENT_SCHEMAS["entity_resolution.completed"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "EntityResolutionCompleted",
    "properties": {
        "source_entity_id": {"type": "string"},
        "target_entity_id": {"type": "string"},
        "match_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "tenant_id": {"type": "string"},
    },
    "required": ["source_entity_id", "target_entity_id", "tenant_id"],
}

EVENT_SCHEMAS["golden_record.created"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "GoldenRecordCreated",
    "properties": {
        "golden_id": {"type": "string"},
        "source_ids": {"type": "array", "items": {"type": "string"}},
        "tenant_id": {"type": "string"},
    },
    "required": ["golden_id", "source_ids", "tenant_id"],
}

# ── CRM / Opportunity ──────────────────────────────────────────────────────

EVENT_SCHEMAS["opportunity.created"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "OpportunityCreated",
    "properties": {
        "opportunity_id": {"type": "string"},
        "company_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "name": {"type": "string"},
        "value": {"type": "number"},
        "stage": {"type": "string"},
    },
    "required": ["opportunity_id", "company_id", "tenant_id", "name"],
}

EVENT_SCHEMAS["opportunity.stage_changed"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "OpportunityStageChanged",
    "properties": {
        "opportunity_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "from_stage": {"type": "string"},
        "to_stage": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["opportunity_id", "tenant_id", "from_stage", "to_stage"],
}

EVENT_SCHEMAS["opportunity.won"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "OpportunityWon",
    "properties": {
        "opportunity_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "value": {"type": "number"},
        "close_date": {"type": "string", "format": "date"},
    },
    "required": ["opportunity_id", "tenant_id", "value"],
}

# ── Scoring & AI ────────────────────────────────────────────────────────────

EVENT_SCHEMAS["company.scored"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "CompanyScored",
    "properties": {
        "company_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "score_type": {"type": "string"},
        "score": {"type": "number", "minimum": 0, "maximum": 100},
        "factors": {"type": "object"},
    },
    "required": ["company_id", "tenant_id", "score_type", "score"],
}

EVENT_SCHEMAS["agent.task_completed"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "AgentTaskCompleted",
    "properties": {
        "task_id": {"type": "string"},
        "agent_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "result_summary": {"type": "string"},
        "duration_ms": {"type": "number"},
    },
    "required": ["task_id", "agent_id", "tenant_id"],
}

# ── Workflow ────────────────────────────────────────────────────────────────

EVENT_SCHEMAS["workflow.triggered"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "WorkflowTriggered",
    "properties": {
        "workflow_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "trigger_event": {"type": "string"},
        "context": {"type": "object"},
    },
    "required": ["workflow_id", "tenant_id", "trigger_event"],
}

EVENT_SCHEMAS["workflow.failed"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "WorkflowFailed",
    "properties": {
        "workflow_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "error": {"type": "string"},
        "step": {"type": "string"},
        "retry_count": {"type": "integer", "minimum": 0},
    },
    "required": ["workflow_id", "tenant_id", "error"],
}

# ── Billing ─────────────────────────────────────────────────────────────────

EVENT_SCHEMAS["subscription.changed"] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "SubscriptionChanged",
    "properties": {
        "tenant_id": {"type": "string"},
        "old_plan": {"type": "string"},
        "new_plan": {"type": "string"},
        "effective_date": {"type": "string", "format": "date"},
    },
    "required": ["tenant_id", "old_plan", "new_plan"],
}


def get_schema(event_type: str) -> dict[str, Any] | None:
    """Get the JSON Schema for an event type, or None if not registered."""
    return EVENT_SCHEMAS.get(event_type)


def validate_event(event: DomainEvent) -> list[str]:
    """Validate an event's data payload against its registered schema.

    Returns a list of validation error messages (empty list = valid).
    If no schema is registered, validation is skipped.
    """
    schema = EVENT_SCHEMAS.get(event.event_type)
    if schema is None:
        return []

    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(event.data))
        return [e.message for e in errors]
    except ImportError:
        return _validate_event_fallback(event.data, schema)
    except Exception as exc:
        logger.warning("Schema validation error for %s: %s", event.event_type, exc)
        return [str(exc)]


def _validate_event_fallback(data: Any, schema: dict[str, Any]) -> list[str]:
    """Minimal required/type checks when jsonschema is not installed."""
    if not isinstance(data, dict):
        return ["data must be an object"]
    errors: list[str] = []
    for key in schema.get("required", []):
        if key not in data:
            errors.append(f"'{key}' is a required property")
    props = schema.get("properties") or {}
    for key, prop in props.items():
        if key not in data:
            continue
        expected = prop.get("type")
        value = data[key]
        if expected == "string" and not isinstance(value, str):
            errors.append(f"'{key}' is not of type 'string'")
        elif expected == "integer" and not isinstance(value, int):
            errors.append(f"'{key}' is not of type 'integer'")
        elif expected == "number" and not isinstance(value, (int, float)):
            errors.append(f"'{key}' is not of type 'number'")
        elif expected == "array" and not isinstance(value, list):
            errors.append(f"'{key}' is not of type 'array'")
        elif expected == "object" and not isinstance(value, dict):
            errors.append(f"'{key}' is not of type 'object'")
        elif expected == "boolean" and not isinstance(value, bool):
            errors.append(f"'{key}' is not of type 'boolean'")
    return errors


def register_schema(event_type: str, schema: dict[str, Any]) -> None:
    """Register a new schema for an event type."""
    EVENT_SCHEMAS[event_type] = schema
    logger.debug("Schema registered for %s", event_type)


def export_schemas() -> dict[str, dict[str, Any]]:
    """Export all registered schemas (for Schema Registry sync)."""
    return dict(EVENT_SCHEMAS)


def export_schemas_json() -> str:
    """Export all schemas as a JSON string."""
    return json.dumps(export_schemas(), indent=2, default=str)
