"""Tenant Studio — CAP-082/083 (STORY-10-01..10-03).

Custom fields + Workflow Builder canvas compiler. Not Production GO.
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
from app.modules.tenant_studio.workflow_canvas import CanvasNode, WorkflowCanvas
from app.modules.tenant_studio.workflow_compiler import (
    WorkflowCanvasCompileError,
    compile_canvas,
)

__all__ = [
    "CUSTOM_FIELDS_BAG_KEY",
    "CanvasNode",
    "CustomFieldDefinition",
    "CustomFieldDefinitionError",
    "CustomObjectSchema",
    "MemCustomFieldDefinitionService",
    "RESERVED_COLUMNS",
    "WorkflowCanvas",
    "WorkflowCanvasCompileError",
    "auto_render_payload",
    "build_auto_render_form",
    "build_field_definition",
    "compile_canvas",
    "is_reserved",
    "merge_custom_field_values",
    "read_custom_field_values",
    "reserved_for",
]
