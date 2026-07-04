"""UI Schema Engine — generates complete UI schemas from Capability Registry + Widget Registry.

Any screen (Company360, Deal360, Dashboard, Form) is produced as a UISchema JSON.
The frontend Renderer reads this JSON and builds the UI. No hardcoded pages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from sdk.frontend_sdk import UISchema, ViewType, UIPolicy, ActionDescriptor, CommandDescriptor


class SchemaVersion(str, Enum):
    V1 = "https://salesos.ai/schemas/ui-v1.json"


@dataclass
class LayoutConfig:
    zones: list[str] = field(default_factory=lambda: ["top", "left", "center", "right", "bottom"])
    defaults: dict[str, list[str]] = field(default_factory=lambda: {
        "left": ["ai_copilot"],
        "center": ["overview", "timeline", "signals"],
    })
    grid: dict = field(default_factory=lambda: {"columns": 12, "gap": "16px"})

    def to_dict(self) -> dict:
        return {"zones": self.zones, "defaults": self.defaults, "grid": self.grid}


@dataclass
class WidgetSchema:
    """A widget within a UISchema."""
    id: str
    renderer: str
    zone: str = "center"
    order: int = 0
    width: int = 4  # grid columns
    height: int = 2  # grid rows
    permissions: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    commands: list[dict] = field(default_factory=list)
    ai_context: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "renderer": self.renderer,
            "zone": self.zone,
            "order": self.order,
            "width": self.width,
            "height": self.height,
            "permissions": self.permissions,
            "config": self.config,
            "commands": self.commands,
            "ai_context": self.ai_context,
        }


class UISchemaEngine:
    """Generates UISchema JSON for any view type."""

    def __init__(self):
        self._schema_registry: dict[str, dict] = {}

    def register_schema(self, view_id: str, schema: dict):
        self._schema_registry[view_id] = schema

    def generate_viewer_schema(self, entity_type: str, entity_id: str,
                               capabilities: list[dict],
                               widgets: list[dict],
                               policies: Optional[list[dict]] = None,
                               user_permissions: Optional[list[str]] = None) -> dict:
        """Generate a complete object viewer schema."""
        resolved_widgets = []
        for w in widgets:
            perms = w.get("permissions", [])
            if user_permissions and perms:
                if not all(p in user_permissions for p in perms):
                    continue
            resolved_widgets.append(WidgetSchema(
                id=w["id"],
                renderer=w.get("renderer", f"{w['id'].title()}Widget"),
                zone=w.get("zone", "center"),
                order=w.get("order", len(resolved_widgets)),
                width=w.get("width", 4),
                height=w.get("height", 2),
                permissions=perms,
                config=w.get("config", {}),
                commands=capabilities[0].get("commands", []) if capabilities else [],
                ai_context={"entity_type": entity_type, "entity_id": entity_id},
            ).to_dict())

        # Build actions from capabilities
        actions = []
        for cap in capabilities:
            for perm in cap.get("contract", {}).get("permissions", []):
                if "create" in perm or "write" in perm:
                    actions.append(ActionDescriptor(
                        id=f"{cap['id']}.{perm}",
                        label=perm.replace(".", " ").title(),
                        handler=f"{cap['id']}.{perm}",
                        permissions=[perm],
                    ).to_dict())

        # Build commands from capabilities
        commands = []
        for cap in capabilities:
            commands.append(CommandDescriptor(
                id=f"go-to-{cap['id']}",
                label=f"Go to {cap['name']}",
                category="navigation",
                context=entity_type,
            ).to_dict())

        ui_policies = policies or []
        if user_permissions:
            for w in resolved_widgets:
                for perm in w.get("permissions", []):
                    if perm not in user_permissions:
                        ui_policies.append(UIPolicy(
                            effect="hide", widget=w["id"], permission=perm
                        ).to_dict())

        schema = UISchema(
            view=ViewType.OBJECT_VIEWER,
            entity_type=entity_type,
            entity_id=entity_id,
            title=f"{entity_type.title()}360",
            layout=LayoutConfig().to_dict(),
            widgets=resolved_widgets,
            actions=actions,
            commands=commands,
            policies=ui_policies,
            ai_context={"entity_type": entity_type, "entity_id": entity_id},
            meta={"schema_version": SchemaVersion.V1.value, "generated_by": "UISchemaEngine"},
        )
        return schema.to_dict()

    def generate_form_schema(self, form_id: str, title: str,
                             schema: dict, ui_schema: Optional[dict] = None) -> dict:
        """Generate a form schema from JSON Schema + UI Schema."""
        return {
            "$schema": SchemaVersion.V1.value,
            "view": ViewType.FORM.value,
            "form_id": form_id,
            "title": title,
            "schema": schema,
            "ui_schema": ui_schema or {},
            "meta": {"generated_by": "UISchemaEngine"},
        }

    def resolve_schema(self, view_id: str, context: Optional[dict] = None) -> Optional[dict]:
        """Resolve a pre-registered schema with optional context injection."""
        schema = self._schema_registry.get(view_id)
        if not schema:
            return None
        if context:
            import json
            schema_str = json.dumps(schema)
            for key, value in context.items():
                schema_str = schema_str.replace(f"${{{key}}}", str(value))
            schema = json.loads(schema_str)
        return schema
