"""STORY-10-02 — Auto-render form schema from CAP-082 definitions.

Produces Form Engine–compatible field descriptors so Company/Contact/Opportunity
UI can render custom fields with zero per-field frontend code.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.modules.tenant_studio.definitions import CustomFieldDefinition, CustomObjectSchema
from runtime.form_engine import FormDefinition, FormField

# Values bag key inside Company/Contact metadata JSONB (and opportunity payload).
CUSTOM_FIELDS_BAG_KEY = "custom_fields"

_TYPE_MAP: dict[str, str] = {
    "string": "string",
    "number": "number",
    "date": "date",
    "enum": "enum",
}


def definition_to_form_field(defn: CustomFieldDefinition, *, order: int = 0) -> FormField:
    enum_opts = None
    if defn.field_type == "enum":
        enum_opts = [{"label": v, "value": v} for v in defn.enum_values]
    return FormField(
        key=defn.field_key,
        type=_TYPE_MAP.get(defn.field_type, "string"),
        label=defn.label or defn.field_key,
        required=False,
        enum=enum_opts,
        order=order,
        section="custom_fields",
        width="half",
    )


def build_auto_render_form(
    schema: CustomObjectSchema,
    *,
    form_id: str | None = None,
    title: str | None = None,
) -> FormDefinition:
    """Build a FormDefinition from a tenant custom-field schema."""
    fields = [
        definition_to_form_field(defn, order=i) for i, defn in enumerate(schema.fields.values())
    ]
    obj = schema.object_key
    return FormDefinition(
        id=form_id or f"custom-fields:{obj}:v{schema.schema_version}",
        title=title or f"Custom fields ({obj})",
        description=(
            "Auto-rendered from CAP-082 definitions — no per-field frontend code. "
            f"schema_version={schema.schema_version}"
        ),
        fields=fields,
        sections=[
            {
                "id": "custom_fields",
                "label": "Custom fields",
                "fields": [f.key for f in fields],
            }
        ]
        if fields
        else [],
    )


def auto_render_payload(
    schema: CustomObjectSchema,
    *,
    values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSON payload for Studio / entity UI auto-render."""
    form = build_auto_render_form(schema)
    out = form.to_dict()
    out["object_key"] = schema.object_key
    out["tenant_id"] = schema.tenant_id
    out["schema_version"] = schema.schema_version
    out["values"] = dict(values or {})
    out["bag_key"] = CUSTOM_FIELDS_BAG_KEY
    out["renderer"] = "custom_fields_auto"  # FE generic section id
    return out


def read_custom_field_values(
    metadata: dict[str, Any] | None,
    definitions: Sequence[CustomFieldDefinition] | None = None,
) -> dict[str, Any]:
    """Read custom field values from metadata[custom_fields] bag."""
    bag = {}
    if isinstance(metadata, dict):
        raw = metadata.get(CUSTOM_FIELDS_BAG_KEY)
        if isinstance(raw, dict):
            bag = dict(raw)
    if not definitions:
        return bag
    allowed = {d.field_key for d in definitions}
    return {k: v for k, v in bag.items() if k in allowed}


def merge_custom_field_values(
    metadata: dict[str, Any] | None,
    updates: dict[str, Any],
    *,
    definitions: Sequence[CustomFieldDefinition],
) -> dict[str, Any]:
    """Merge updates into metadata custom_fields bag (known keys only)."""
    base = dict(metadata or {})
    current = read_custom_field_values(base, definitions=None)
    allowed = {d.field_key for d in definitions}
    for key, val in (updates or {}).items():
        k = str(key).strip()
        if k not in allowed:
            continue
        if val is None:
            current.pop(k, None)
        else:
            current[k] = val
    base[CUSTOM_FIELDS_BAG_KEY] = current
    return base
