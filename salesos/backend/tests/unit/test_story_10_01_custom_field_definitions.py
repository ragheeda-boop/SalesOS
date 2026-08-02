"""STORY-10-01 — Custom field definitions (reserved collision + versioned schema)."""

from __future__ import annotations

import pytest

from app.modules.tenant_studio.definitions import (
    CustomFieldDefinitionError,
    build_field_definition,
)
from app.modules.tenant_studio.reserved_columns import is_reserved
from app.modules.tenant_studio.service import MemCustomFieldDefinitionService


def test_reserved_column_collision_rejected() -> None:
    assert is_reserved("company", "cr_number") is True
    with pytest.raises(CustomFieldDefinitionError, match="collides with reserved"):
        build_field_definition(
            tenant_id="t1",
            object_key="company",
            field_key="cr_number",
            field_type="string",
            label="CR",
            schema_version=1,
        )


def test_define_scalar_field_bumps_schema_version() -> None:
    svc = MemCustomFieldDefinitionService()
    f1 = svc.define_field(
        tenant_id="t-a",
        object_key="company",
        field_key="segment_tier",
        field_type="enum",
        label="Segment",
        enum_values=["A", "B"],
    )
    assert f1.schema_version == 1
    assert f1.field_type == "enum"
    schema = svc.get_schema(tenant_id="t-a", object_key="company")
    assert schema.schema_version == 1
    assert "segment_tier" in schema.fields

    f2 = svc.define_field(
        tenant_id="t-a",
        object_key="company",
        field_key="renewal_date",
        field_type="date",
        label="Renewal",
    )
    assert f2.schema_version == 2
    assert svc.get_schema(tenant_id="t-a", object_key="company").schema_version == 2


def test_duplicate_field_key_rejected() -> None:
    svc = MemCustomFieldDefinitionService()
    svc.define_field(
        tenant_id="t-a",
        object_key="contact",
        field_key="linkedin_url",
        field_type="string",
    )
    with pytest.raises(CustomFieldDefinitionError, match="already defined"):
        svc.define_field(
            tenant_id="t-a",
            object_key="contact",
            field_key="linkedin_url",
            field_type="string",
        )


def test_tenant_isolation_same_field_key() -> None:
    """AC: multi-tenant define conflicting-looking keys — isolated schemas."""
    svc = MemCustomFieldDefinitionService()
    a = svc.define_field(
        tenant_id="tenant-1",
        object_key="opportunity",
        field_key="deal_code",
        field_type="string",
    )
    b = svc.define_field(
        tenant_id="tenant-2",
        object_key="opportunity",
        field_key="deal_code",
        field_type="number",
    )
    assert a.tenant_id == "tenant-1"
    assert b.tenant_id == "tenant-2"
    assert a.field_type == "string"
    assert b.field_type == "number"
    assert len(svc.list_fields(tenant_id="tenant-1", object_key="opportunity")) == 1
    assert len(svc.list_fields(tenant_id="tenant-2", object_key="opportunity")) == 1


def test_enum_requires_values() -> None:
    with pytest.raises(CustomFieldDefinitionError, match="enum_values"):
        build_field_definition(
            tenant_id="t1",
            object_key="company",
            field_key="tier_x",
            field_type="enum",
            label="Tier",
            schema_version=1,
            enum_values=[],
        )
