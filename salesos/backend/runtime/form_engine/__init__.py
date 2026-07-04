"""Form Engine — generates dynamic forms from JSON Schema + UI Schema.

Every form is defined as data:
  - schema: JSON Schema defining fields, types, validation
  - ui_schema: Layout, order, visibility, translations

No hardcoded forms. Every Create Company, Edit Contact, Filter Search is a schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FormField:
    """A single form field derived from JSON Schema."""
    key: str
    type: str  # string, number, boolean, date, enum, object, array, email, tel, url
    label: str
    label_ar: Optional[str] = None
    placeholder: Optional[str] = None
    placeholder_ar: Optional[str] = None
    required: bool = False
    default: Any = None
    enum: Optional[list[dict]] = None  # [{"label": "...", "value": "..."}]
    validation: dict = field(default_factory=dict)
    visible: bool = True
    disabled: bool = False
    order: int = 0
    width: str = "full"  # full, half, third
    section: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "type": self.type,
            "label": self.label,
            "label_ar": self.label_ar or self.label,
            "placeholder": self.placeholder,
            "placeholder_ar": self.placeholder_ar,
            "required": self.required,
            "default": self.default,
            "enum": self.enum,
            "validation": self.validation,
            "visible": self.visible,
            "disabled": self.disabled,
            "order": self.order,
            "width": self.width,
            "section": self.section,
        }


@dataclass
class FormDefinition:
    """A complete form definition generated from schema."""
    id: str
    title: str
    title_ar: Optional[str] = None
    description: Optional[str] = None
    fields: list[FormField] = field(default_factory=list)
    submit_label: str = "Save"
    submit_label_ar: str = "حفظ"
    cancel_label: str = "Cancel"
    cancel_label_ar: str = "إلغاء"
    sections: list[dict] = field(default_factory=list)  # [{"id": "...", "label": "...", "fields": [...]}]
    policies: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "title_ar": self.title_ar or self.title,
            "description": self.description,
            "fields": [f.to_dict() for f in sorted(self.fields, key=lambda x: x.order)],
            "submit_label": self.submit_label,
            "submit_label_ar": self.submit_label_ar,
            "cancel_label": self.cancel_label,
            "cancel_label_ar": self.cancel_label_ar,
            "sections": self.sections,
            "policies": self.policies,
        }


JSON_SCHEMA_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "integer": "number",
    "boolean": "boolean",
    "array": "array",
    "object": "object",
}


class FormEngine:
    """Generates form definitions from JSON Schema."""

    def __init__(self):
        self._form_registry: dict[str, FormDefinition] = {}

    def register_form(self, form_id: str, form: FormDefinition):
        self._form_registry[form_id] = form

    def generate_from_schema(self, form_id: str, title: str,
                             schema: dict,
                             ui_schema: Optional[dict] = None) -> FormDefinition:
        """Generate a FormDefinition from JSON Schema + optional UI Schema."""
        fields = []
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        for i, (key, prop) in enumerate(properties.items()):
            json_type = prop.get("type", "string")
            field_type = JSON_SCHEMA_TYPE_MAP.get(json_type, "string")

            # Map format
            fmt = prop.get("format", "")
            if fmt == "email":
                field_type = "email"
            elif fmt == "uri" or fmt == "url":
                field_type = "url"
            elif fmt == "date":
                field_type = "date"
            elif fmt == "date-time":
                field_type = "datetime"

            # Enum
            enum_vals = None
            if prop.get("enum"):
                enum_vals = [{"label": str(v), "value": v} for v in prop["enum"]]

            # UI Schema overrides
            ui_override = {}
            if ui_schema:
                ui_override = ui_schema.get(key, {})

            field = FormField(
                key=key,
                type=field_type,
                label=ui_override.get("label", prop.get("title", key.replace("_", " ").title())),
                label_ar=ui_override.get("label_ar"),
                placeholder=ui_override.get("placeholder"),
                required=key in required_fields,
                default=prop.get("default"),
                enum=enum_vals,
                validation={
                    "min_length": prop.get("minLength"),
                    "max_length": prop.get("maxLength"),
                    "minimum": prop.get("minimum"),
                    "maximum": prop.get("maximum"),
                    "pattern": prop.get("pattern"),
                },
                visible=ui_override.get("visible", True),
                disabled=ui_override.get("disabled", False),
                order=ui_override.get("order", i),
                width=ui_override.get("width", "full"),
                section=ui_override.get("section"),
            )
            fields.append(field)

        form = FormDefinition(
            id=form_id,
            title=title,
            title_ar=ui_schema.get("title_ar") if ui_schema else None,
            description=schema.get("description"),
            fields=fields,
            sections=ui_schema.get("sections", []) if ui_schema else [],
            policies=ui_schema.get("policies", []) if ui_schema else [],
        )
        self._form_registry[form_id] = form
        return form

    def get_form(self, form_id: str) -> Optional[FormDefinition]:
        return self._form_registry.get(form_id)

    def validate(self, form_id: str, data: dict) -> tuple[bool, list[str]]:
        """Validate form data against the schema."""
        form = self._form_registry.get(form_id)
        if not form:
            return False, ["Form not found"]

        errors = []
        for field in form.fields:
            value = data.get(field.key)
            if field.required and (value is None or value == ""):
                errors.append(f"{field.label} is required")
            if value is not None:
                if field.validation.get("min_length") and isinstance(value, str):
                    if len(value) < field.validation["min_length"]:
                        errors.append(f"{field.label} must be at least {field.validation['min_length']} characters")
                if field.validation.get("max_length") and isinstance(value, str):
                    if len(value) > field.validation["max_length"]:
                        errors.append(f"{field.label} must be at most {field.validation['max_length']} characters")
        return len(errors) == 0, errors
