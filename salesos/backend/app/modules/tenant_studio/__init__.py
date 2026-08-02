"""Tenant Studio — CAP-082/083/085/003 (STORY-10-01..10-04, 10-06).

Custom fields + Workflow Builder + Scoring Rules + Permissions. Not Production GO.
"""

from app.modules.tenant_studio.auto_render import (
    CUSTOM_FIELDS_BAG_KEY,
    auto_render_payload,
    build_auto_render_form,
    merge_custom_field_values,
    read_custom_field_values,
)
from app.modules.tenant_studio.custom_roles import CustomRole, CustomRoleError
from app.modules.tenant_studio.definitions import (
    CustomFieldDefinition,
    CustomFieldDefinitionError,
    CustomObjectSchema,
    build_field_definition,
)
from app.modules.tenant_studio.permission_ceiling import (
    PermissionCeilingError,
    assert_within_ceiling,
)
from app.modules.tenant_studio.reserved_columns import (
    RESERVED_COLUMNS,
    is_reserved,
    reserved_for,
)
from app.modules.tenant_studio.scoring_rules import (
    PLATFORM_DEFAULT_WEIGHTS,
    ScoringRule,
    ScoringRuleError,
)
from app.modules.tenant_studio.scoring_rules_engine import (
    evaluate_score,
    get_effective_dimension_weights,
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
    "CustomRole",
    "CustomRoleError",
    "MemCustomFieldDefinitionService",
    "PLATFORM_DEFAULT_WEIGHTS",
    "PermissionCeilingError",
    "RESERVED_COLUMNS",
    "ScoringRule",
    "ScoringRuleError",
    "WorkflowCanvas",
    "WorkflowCanvasCompileError",
    "assert_within_ceiling",
    "auto_render_payload",
    "build_auto_render_form",
    "build_field_definition",
    "compile_canvas",
    "evaluate_score",
    "get_effective_dimension_weights",
    "is_reserved",
    "merge_custom_field_values",
    "read_custom_field_values",
    "reserved_for",
]
