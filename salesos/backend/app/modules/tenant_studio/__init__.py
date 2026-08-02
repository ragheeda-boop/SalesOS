"""Tenant Studio — CAP-082 Custom Objects/Fields (STORY-10-01/10-02).

Definition + auto-render form schema. Not Production GO.
"""

from app.modules.tenant_studio.auto_render import (
    CUSTOM_FIELDS_BAG_KEY,
    auto_render_payload,
    build_auto_render_form,
    merge_custom_field_values,
    read_custom_field_values,
)
from app.modules.tenant_studio.definitions import (
    CustomFieldDefinition,
    CustomFieldDefinitionError,
    CustomObjectSchema,
    build_field_definition,
)
from app.modules.tenant_studio.reserved_columns import (
    RESERVED_COLUMNS,
    is_reserved,
    reserved_for,
)
from app.modules.tenant_studio.service import MemCustomFieldDefinitionService

__all__ = [
    "CUSTOM_FIELDS_BAG_KEY",
    "CustomFieldDefinition",
    "CustomFieldDefinitionError",
    "CustomObjectSchema",
    "MemCustomFieldDefinitionService",
    "RESERVED_COLUMNS",
    "auto_render_payload",
    "build_auto_render_form",
    "build_field_definition",
    "is_reserved",
    "merge_custom_field_values",
    "read_custom_field_values",
    "reserved_for",
]
