"""STORY-10-02 — Custom field auto-render form schema + value bag helpers."""

from __future__ import annotations

from app.modules.tenant_studio.auto_render import (
    CUSTOM_FIELDS_BAG_KEY,
    auto_render_payload,
    build_auto_render_form,
    merge_custom_field_values,
    read_custom_field_values,
)
from app.modules.tenant_studio.service import MemCustomFieldDefinitionService


def test_auto_render_form_includes_defined_fields() -> None:
    """AC: defined fields appear in form schema — zero per-field FE code needed."""
    svc = MemCustomFieldDefinitionService()
    svc.define_field(
        tenant_id="t1",
        object_key="company",
        field_key="segment_tier",
        field_type="enum",
        label="Segment",
        enum_values=["A", "B"],
    )
    svc.define_field(
        tenant_id="t1",
        object_key="company",
        field_key="renewal_date",
        field_type="date",
        label="Renewal",
    )
    schema = svc.get_schema(tenant_id="t1", object_key="company")
    form = build_auto_render_form(schema)
    keys = [f.key for f in form.fields]
    assert keys == ["segment_tier", "renewal_date"]
    segment = form.fields[0]
    assert segment.type == "enum"
    assert segment.section == "custom_fields"
    assert segment.enum == [{"label": "A", "value": "A"}, {"label": "B", "value": "B"}]

    payload = auto_render_payload(schema, values={"segment_tier": "A"})
    assert payload["renderer"] == "custom_fields_auto"
    assert payload["bag_key"] == CUSTOM_FIELDS_BAG_KEY
    assert payload["schema_version"] == 2
    assert payload["values"]["segment_tier"] == "A"
    assert len(payload["fields"]) == 2


def test_custom_field_values_round_trip_in_metadata_bag() -> None:
    svc = MemCustomFieldDefinitionService()
    svc.define_field(
        tenant_id="t1",
        object_key="contact",
        field_key="linkedin_url",
        field_type="string",
    )
    defs = svc.list_fields(tenant_id="t1", object_key="contact")
    merged = merge_custom_field_values(
        {"note": "keep"},
        {"linkedin_url": "https://example.com/in/x", "cr_number": "shadow"},
        definitions=defs,
    )
    assert merged["note"] == "keep"
    assert CUSTOM_FIELDS_BAG_KEY in merged
    assert merged[CUSTOM_FIELDS_BAG_KEY]["linkedin_url"] == "https://example.com/in/x"
    # Unknown / reserved-looking keys not in definitions are dropped.
    assert "cr_number" not in merged[CUSTOM_FIELDS_BAG_KEY]
    values = read_custom_field_values(merged, definitions=defs)
    assert values == {"linkedin_url": "https://example.com/in/x"}


def test_auto_render_empty_schema() -> None:
    svc = MemCustomFieldDefinitionService()
    schema = svc.get_schema(tenant_id="t-empty", object_key="opportunity")
    payload = auto_render_payload(schema)
    assert payload["fields"] == []
    assert payload["schema_version"] == 0
    assert payload["object_key"] == "opportunity"
