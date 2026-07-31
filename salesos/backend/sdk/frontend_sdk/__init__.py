"""Frontend SDK — typed interfaces for consuming the platform from any frontend framework.

Provides: UI Schema types, Action client, Command palette, Theme consumer, Object Viewer client.
Not tied to React/Vue/Angular — works with any framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ViewType(str, Enum):
    OBJECT_VIEWER = "object-viewer"
    DASHBOARD = "dashboard"
    FORM = "form"
    LIST = "list"
    SETTINGS = "settings"
    WORKSPACE = "workspace"


@dataclass
class UISchema:
    """A complete UI definition for any screen. No JSX — just JSON."""

    view: ViewType = ViewType.OBJECT_VIEWER
    entity_type: str | None = None
    entity_id: str | None = None
    title: str | None = None
    layout: dict = field(default_factory=lambda: {"zones": ["center"]})
    widgets: list[dict] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    commands: list[dict] = field(default_factory=list)
    policies: list[dict] = field(default_factory=list)
    ai_context: dict | None = None
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "view": self.view.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "title": self.title,
            "layout": self.layout,
            "widgets": self.widgets,
            "actions": self.actions,
            "commands": self.commands,
            "policies": self.policies,
            "ai_context": self.ai_context,
            "meta": self.meta,
        }


@dataclass
class ActionDescriptor:
    """An action that any frontend framework can render as a button/menu item."""

    id: str
    label: str
    label_ar: str | None = None
    icon: str | None = None
    variant: str = "default"  # default, primary, danger, ghost
    shortcut: str | None = None
    schema: dict | None = None  # JSON Schema if action requires input
    confirm: str | None = None  # Confirmation message
    permissions: list[str] = field(default_factory=list)
    handler: str | None = None  # Action handler ID (resolved by Action Engine)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "label_ar": self.label_ar,
            "icon": self.icon,
            "variant": self.variant,
            "shortcut": self.shortcut,
            "schema": self.schema,
            "confirm": self.confirm,
            "permissions": self.permissions,
            "handler": self.handler,
        }


@dataclass
class CommandDescriptor:
    """A command for the Global Command Bar (Ctrl+K)."""

    id: str
    label: str
    label_ar: str | None = None
    description: str | None = None
    icon: str | None = None
    category: str = "general"
    shortcut: str | None = None
    context: str | None = None
    permissions: list[str] = field(default_factory=list)
    schema: dict | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "label_ar": self.label_ar,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "shortcut": self.shortcut,
            "context": self.context,
            "permissions": self.permissions,
            "schema": self.schema,
        }


@dataclass
class UIPolicy:
    """Declarative UI policy — hide, disable, or modify widgets based on conditions."""

    effect: str  # "hide", "disable", "require", "modify"
    widget: str | None = None
    role: str | None = None
    permission: str | None = None
    condition: str | None = None  # Expression evaluated by Policy Engine

    def to_dict(self) -> dict:
        return {
            "effect": self.effect,
            "widget": self.widget,
            "role": self.role,
            "permission": self.permission,
            "condition": self.condition,
        }


def build_ui_schema(
    view_type: ViewType,
    entity_type: str | None = None,
    entity_id: str | None = None,
    widgets: list[dict] | None = None,
    actions: list[dict] | None = None,
    policies: list[dict] | None = None,
) -> dict:
    """Helper to build a UISchema from parts."""
    schema = UISchema(
        view=view_type,
        entity_type=entity_type,
        entity_id=entity_id,
        widgets=widgets or [],
        actions=actions or [],
        policies=policies or [],
    )
    return schema.to_dict()
