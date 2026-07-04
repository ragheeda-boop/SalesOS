"""Widget SDK — build, register, and configure widgets without touching the runtime.

Widgets are the atomic unit of UI in XP1.
This SDK provides everything a widget developer needs:
  - WidgetDefinition builder
  - Slot resolver
  - Permission checker
  - Config schema builder
  - AI context declarer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class WidgetSlot(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    FULL = "full"


class WidgetSize(str, Enum):
    FULL = "full"
    HALF = "half"
    THIRD = "third"
    QUARTER = "quarter"


@dataclass
class WidgetDefinition:
    """Complete definition of a widget for registration."""
    id: str
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    renderer: str = ""  # Frontend component name
    capability_id: str = ""
    slots: list[WidgetSlot] = field(default_factory=lambda: [WidgetSlot.CENTER])
    default_size: WidgetSize = WidgetSize.FULL
    permissions: list[str] = field(default_factory=list)
    config_schema: Optional[dict] = None  # JSON Schema for widget config
    commands: list[dict] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    ai_context: Optional[dict] = None  # What AI knows when this widget is active
    feature_flags: list[str] = field(default_factory=list)
    icon: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "renderer": self.renderer,
            "capability_id": self.capability_id,
            "slots": [s.value for s in self.slots],
            "default_size": self.default_size.value,
            "permissions": self.permissions,
            "config_schema": self.config_schema,
            "commands": self.commands,
            "events": self.events,
            "dependencies": self.dependencies,
            "ai_context": self.ai_context,
            "feature_flags": self.feature_flags,
            "icon": self.icon,
            "tags": self.tags,
        }


class WidgetBuilder:
    """Fluent builder for creating widget definitions."""

    def __init__(self, widget_id: str, renderer: str):
        self._widget = WidgetDefinition(id=widget_id, renderer=renderer, name=widget_id)

    def named(self, name: str) -> "WidgetBuilder":
        self._widget.name = name
        return self

    def described(self, description: str) -> "WidgetBuilder":
        self._widget.description = description
        return self

    def version(self, version: str) -> "WidgetBuilder":
        self._widget.version = version
        return self

    def for_capability(self, cap_id: str) -> "WidgetBuilder":
        self._widget.capability_id = cap_id
        return self

    def in_slots(self, *slots: WidgetSlot) -> "WidgetBuilder":
        self._widget.slots = list(slots)
        return self

    def sized(self, size: WidgetSize) -> "WidgetBuilder":
        self._widget.default_size = size
        return self

    def requires_permissions(self, *perms: str) -> "WidgetBuilder":
        self._widget.permissions = list(perms)
        return self

    def with_config(self, schema: dict) -> "WidgetBuilder":
        self._widget.config_schema = schema
        return self

    def with_ai_context(self, ctx: dict) -> "WidgetBuilder":
        self._widget.ai_context = ctx
        return self

    def tagged(self, *tags: str) -> "WidgetBuilder":
        self._widget.tags = list(tags)
        return self

    def build(self) -> WidgetDefinition:
        return self._widget


def create_widget(widget_id: str, renderer: str) -> WidgetBuilder:
    """Entry point: create a new widget definition."""
    return WidgetBuilder(widget_id, renderer)
