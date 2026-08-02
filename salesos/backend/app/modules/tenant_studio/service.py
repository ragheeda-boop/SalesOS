"""STORY-10-01 — Tenant-scoped custom field definition service (in-memory).

No Alembic / FORCE RLS (POLICY_COUNT stays 71). Persistence via Postgres table
is a follow-on. Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.tenant_studio.definitions import (
    CustomFieldDefinition,
    CustomFieldDefinitionError,
    CustomObjectSchema,
    build_field_definition,
)


@dataclass
class MemCustomFieldDefinitionService:
    """In-memory CAP-082 definition store — tenant isolation at app layer."""

    _schemas: dict[str, CustomObjectSchema] = field(default_factory=dict)

    @staticmethod
    def _key(tenant_id: str, object_key: str) -> str:
        return f"{tenant_id}:{object_key}"

    def get_schema(self, *, tenant_id: str, object_key: str) -> CustomObjectSchema:
        tid = str(tenant_id).strip()
        obj = (object_key or "").strip().lower()
        key = self._key(tid, obj)
        schema = self._schemas.get(key)
        if schema is None:
            schema = CustomObjectSchema(tenant_id=tid, object_key=obj, schema_version=0)
            self._schemas[key] = schema
        return schema

    def list_fields(self, *, tenant_id: str, object_key: str) -> list[CustomFieldDefinition]:
        schema = self.get_schema(tenant_id=tenant_id, object_key=object_key)
        return list(schema.fields.values())

    def define_field(
        self,
        *,
        tenant_id: str,
        object_key: str,
        field_key: str,
        field_type: str,
        label: str = "",
        enum_values: list[str] | None = None,
    ) -> CustomFieldDefinition:
        schema = self.get_schema(tenant_id=tenant_id, object_key=object_key)
        # Collision against reserved + existing field keys.
        try:
            candidate = build_field_definition(
                tenant_id=tenant_id,
                object_key=object_key,
                field_key=field_key,
                field_type=field_type,
                label=label,
                schema_version=schema.schema_version + 1,
                enum_values=enum_values,
            )
        except CustomFieldDefinitionError:
            raise
        if candidate.field_key in schema.fields:
            raise CustomFieldDefinitionError(
                f"field_key {candidate.field_key!r} already defined on "
                f"{schema.object_key} for this tenant"
            )
        schema.schema_version = candidate.schema_version
        schema.fields[candidate.field_key] = candidate
        return candidate


# Process-local singleton shared by Studio HTTP (no Alembic).
DEFAULT_STORE = MemCustomFieldDefinitionService()
