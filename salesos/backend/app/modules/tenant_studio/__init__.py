"""Tenant Studio — CAP-082 Custom Objects/Fields (STORY-10-01).

Definition mechanism only. Not Production GO.
"""

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
    "CustomFieldDefinition",
    "CustomFieldDefinitionError",
    "CustomObjectSchema",
    "MemCustomFieldDefinitionService",
    "RESERVED_COLUMNS",
    "build_field_definition",
    "is_reserved",
    "reserved_for",
]
