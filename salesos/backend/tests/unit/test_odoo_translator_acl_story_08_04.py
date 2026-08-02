"""STORY-08-04 — OdooTranslator ACL: six internal responsibilities + loud Validator."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.modules.integration_hub.anti_corruption import (
    AclValidationError,
    OdooTranslator,
)
from app.modules.integration_hub.field_mapping import parse_field_mappings

_MAPPINGS = [
    {"internal": "name", "external": "display_name", "direction": "pull"},
    {"internal": "email", "external": "email_from", "direction": "pull"},
    {"internal": "cr_number", "external": "x_cr", "direction": "pull"},
    {"internal": "stage", "external": "stage_id", "direction": "pull"},
    {"internal": "amount", "external": "expected_revenue", "direction": "pull"},
    {"internal": "note", "external": "description", "direction": "pull"},
    {"internal": "phone", "external": "phone", "direction": "pull"},
    {"internal": "risk_score", "external": "x_ai_risk", "direction": "pull"},
]


def _translator() -> OdooTranslator:
    return OdooTranslator(
        stage_map={"1": "new", "2": "qualified", "won": "closed_won"},
    )


def _raw(**overrides: object) -> dict:
    base: dict = {
        "display_name": "Acme Co",
        "email_from": "a@example.com",
        "x_cr": "1234567890",
        "stage_id": "2",
        "expected_revenue": "12.50",
        "description": "<p>Hello <b>world</b></p>",
        "phone": "+966 50 123 4567",
        "x_ai_risk": 0.9,
    }
    base.update(overrides)
    return base


def test_mapper_projects_external_to_internal() -> None:
    t = _translator()
    mapped = t._map(_raw(), parse_field_mappings(_MAPPINGS))
    assert mapped["name"] == "Acme Co"
    assert mapped["email"] == "a@example.com"
    assert "display_name" not in mapped


def test_validator_rejects_malformed_loudly_not_silent_null() -> None:
    """Demo AC: malformed record fails at Validator with clear error."""
    t = _translator()
    with pytest.raises(AclValidationError, match="required field 'name'") as ei:
        t.translate(
            _raw(display_name=""),
            mappings=_MAPPINGS,
            sync_run_id="run-1",
        )
    assert ei.value.field == "name"
    with pytest.raises(AclValidationError, match="cr_number"):
        t.translate(
            _raw(x_cr="bad"),
            mappings=_MAPPINGS,
            sync_run_id="run-1",
        )
    with pytest.raises(AclValidationError, match="amount"):
        t.translate(
            _raw(expected_revenue="-1"),
            mappings=_MAPPINGS,
            sync_run_id="run-1",
        )


def test_transformer_maps_stage_enums() -> None:
    t = _translator()
    out = t._transform({"stage": "2", "name": "x"})
    assert out["stage"] == "qualified"


def test_normalizer_strips_html_phone_and_minor_units() -> None:
    t = _translator()
    out = t._normalize(
        {
            "note": "<p>Hello <b>world</b></p>",
            "phone": "+966 50 123 4567",
            "amount": 12.5,
            "name": "  Acme   Co ",
        }
    )
    assert out["note"] == "Hello world"
    assert out["phone"] == "966501234567"
    assert out["amount_minor"] == 1250
    assert out["name"] == "Acme Co"


def test_conflict_resolver_salesos_keeps_ai_source_wins_ops() -> None:
    t = _translator()
    merged = t._resolve_conflicts(
        {"name": "FromOdoo", "risk_score": 0.1, "email": "new@x.com"},
        {"name": "Old", "risk_score": 0.99, "email": "old@x.com"},
    )
    assert merged["name"] == "FromOdoo"
    assert merged["email"] == "new@x.com"
    assert merged["risk_score"] == 0.99  # SalesOS-authored retained


def test_versioning_stamps_sync_metadata() -> None:
    t = _translator()
    at = datetime(2026, 8, 2, 5, 0, tzinfo=UTC)
    rec = t._version({"name": "x"}, source_updated_at=at, sync_run_id="sr-9")
    assert rec.sync_run_id == "sr-9"
    assert rec.source_updated_at == at
    assert rec.meta["stages"] == 6


def test_full_pipeline_happy_path() -> None:
    t = _translator()
    rec = t.translate(
        _raw(),
        mappings=_MAPPINGS,
        sync_run_id="run-42",
        source_updated_at=datetime(2026, 8, 1, tzinfo=UTC),
        existing_canonical={"risk_score": 0.77, "name": "Prior"},
    )
    assert rec.payload["name"] == "Acme Co"
    assert rec.payload["stage"] == "qualified"
    assert rec.payload["note"] == "Hello world"
    assert rec.payload["risk_score"] == 0.77
    assert rec.sync_run_id == "run-42"
