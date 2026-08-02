"""STORY-10-01 — Custom field definition shapes + versioned schema validation.

JSONB-column-based CAP-082 (values live under metadata/custom_fields later).
Scalar types only in v1. Collision-checked vs reserved columns. Not Production GO.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from app.modules.tenant_studio.reserved_columns import (
    SUPPORTED_OBJECT_KEYS,
    is_reserved,
    reserved_for,
)

FieldType = Literal["string", "number", "date", "enum"]
SUPPORTED_FIELD_TYPES: frozenset[str] = frozenset({"string", "number", "date", "enum"})

_FIELD_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class CustomFieldDefinitionError(ValueError):
    """Raised when a custom field definition is rejected."""


@dataclass(frozen=True)
class CustomFieldDefinition:
    """OBJ-341 CustomFieldDefinition (definition-only; no value storage here)."""

    id: str
    tenant_id: str
    object_key: str
    field_key: str
    field_type: FieldType
    label: str
    schema_version: int
    enum_values: tuple[str, ...] = ()
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "object_key": self.object_key,
            "field_key": self.field_key,
            "field_type": self.field_type,
            "label": self.label,
            "schema_version": self.schema_version,
            "enum_values": list(self.enum_values),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CustomObjectSchema:
    """Versioned schema for one tenant object (company|contact|opportunity)."""

    tenant_id: str
    object_key: str
    schema_version: int = 0
    fields: dict[str, CustomFieldDefinition] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "object_key": self.object_key,
            "schema_version": self.schema_version,
            "fields": [f.as_dict() for f in self.fields.values()],
        }


def validate_field_key(object_key: str, field_key: str) -> str:
    key = (field_key or "").strip().lower()
    obj = (object_key or "").strip().lower()
    if obj not in SUPPORTED_OBJECT_KEYS:
        raise CustomFieldDefinitionError(
            f"unsupported object_key {object_key!r}; expected company|contact|opportunity"
        )
    if not _FIELD_KEY_RE.match(key):
        raise CustomFieldDefinitionError(
            f"field_key {field_key!r} must match {_FIELD_KEY_RE.pattern}"
        )
    if is_reserved(obj, key):
        raise CustomFieldDefinitionError(
            f"field_key {key!r} collides with reserved {obj} column "
            f"(reserved sample: {sorted(reserved_for(obj))[:8]}...)"
        )
    return key


def validate_field_type(field_type: str, enum_values: list[str] | None) -> FieldType:
    ft = (field_type or "").strip().lower()
    if ft not in SUPPORTED_FIELD_TYPES:
        raise CustomFieldDefinitionError(
            f"field_type {field_type!r} unsupported; v1 allows string|number|date|enum"
        )
    if ft == "enum":
        vals = [str(v).strip() for v in (enum_values or []) if str(v).strip()]
        if not vals:
            raise CustomFieldDefinitionError("enum field_type requires non-empty enum_values")
        return "enum"  # type: ignore[return-value]
    if enum_values:
        raise CustomFieldDefinitionError("enum_values only allowed for field_type=enum")
    return ft  # type: ignore[return-value]


def build_field_definition(
    *,
    tenant_id: str,
    object_key: str,
    field_key: str,
    field_type: str,
    label: str,
    schema_version: int,
    enum_values: list[str] | None = None,
    field_id: str | None = None,
) -> CustomFieldDefinition:
    tid = str(tenant_id).strip()
    if not tid:
        raise CustomFieldDefinitionError("tenant_id required")
    obj = (object_key or "").strip().lower()
    key = validate_field_key(obj, field_key)
    ft = validate_field_type(field_type, enum_values)
    lbl = (label or "").strip() or key
    if schema_version < 1:
        raise CustomFieldDefinitionError("schema_version must be >= 1")
    now = datetime.now(UTC).isoformat()
    enums = (
        tuple(str(v).strip() for v in (enum_values or []) if str(v).strip()) if ft == "enum" else ()
    )
    return CustomFieldDefinition(
        id=field_id or str(uuid.uuid4()),
        tenant_id=tid,
        object_key=obj,
        field_key=key,
        field_type=ft,
        label=lbl,
        schema_version=int(schema_version),
        enum_values=enums,
        created_at=now,
        updated_at=now,
    )
