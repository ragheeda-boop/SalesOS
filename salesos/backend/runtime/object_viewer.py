"""Universal Object Viewer — the template for every 360 view.

Company360, Deal360, Contact360, License360, etc. are all instances of this viewer.
It dynamically generates tabs, widgets, and layouts from:
  - Capability Registry (what capabilities apply to this entity type)
  - Widget Registry (available widget types for each capability)
  - Layout Runtime (user's saved layout customization)
  - Permission Engine (which widgets the user can see)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from runtime.capability_framework import Capability
from runtime.widget_engine import WidgetDefinition, WidgetRegistry, WidgetSlot

from runtime.ux_runtime import UXRuntime


class EntityType(str, Enum):
    COMPANY = "company"
    CONTACT = "contact"
    DEAL = "deal"
    LICENSE = "license"
    BRANCH = "branch"
    PRODUCT = "product"
    WORKSPACE = "workspace"


ENTITY_CAPABILITY_MAP: dict[EntityType, list[str]] = {
    EntityType.COMPANY: ["company", "timeline", "knowledge-graph", "feature-store",
                         "decision-engine", "search", "identity"],
    EntityType.CONTACT: ["company", "timeline", "identity"],
    EntityType.DEAL: ["company", "timeline", "decision-engine", "identity"],
    EntityType.LICENSE: ["company", "timeline"],
    EntityType.BRANCH: ["company", "timeline"],
    EntityType.PRODUCT: ["company"],
    EntityType.WORKSPACE: ["identity", "search", "capability-framework"],
}


@dataclass
class ViewerTab:
    id: str
    label: str
    widget_ids: list[str]
    icon: Optional[str] = None
    order: int = 0
    default: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "widget_ids": self.widget_ids,
            "icon": self.icon,
            "order": self.order,
            "default": self.default,
        }


@dataclass
class ViewerConfig:
    """Complete configuration for rendering an Object Viewer."""
    entity_type: EntityType
    entity_id: str
    tabs: list[ViewerTab] = field(default_factory=list)
    available_widgets: list[WidgetDefinition] = field(default_factory=list)
    zones: list[str] = field(default_factory=lambda: ["top", "left", "center", "right", "bottom"])
    default_layout: dict[str, list[str]] = field(default_factory=lambda: {
        "top": [],
        "left": ["ai_copilot"],
        "center": ["overview", "timeline", "signals"],
        "right": ["recommendations", "feature_scores"],
        "bottom": [],
    })
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "tabs": [t.to_dict() for t in self.tabs],
            "available_widgets": [w.to_dict() for w in self.available_widgets],
            "zones": self.zones,
            "default_layout": self.default_layout,
            "context": self.context,
        }


class UniversalObjectViewer:
    """Generates viewer configurations for any entity type."""

    def __init__(self, ux: UXRuntime):
        self.ux = ux

    def get_viewer(self, entity_type: EntityType, entity_id: str,
                   user_id: str, tenant_id: str,
                   permissions: Optional[list[str]] = None) -> ViewerConfig:
        """Generate a complete viewer configuration."""
        # 1. Determine applicable capabilities
        cap_ids = ENTITY_CAPABILITY_MAP.get(entity_type, [])
        caps = [c for c in Capability.all() if c.id in cap_ids]

        # 2. Get or auto-generate widgets
        WidgetRegistry.generate_from_capabilities()

        # 3. Collect applicable widgets
        available_widgets: list[WidgetDefinition] = []
        for cap in caps:
            for w in WidgetRegistry.by_capability(cap.id):
                available_widgets.append(w)

        # Also add generic widgets
        for w in WidgetRegistry.all():
            if w not in available_widgets and w.tags:
                if entity_type.value in w.tags:
                    available_widgets.append(w)

        # 4. Filter by permissions
        if permissions:
            available_widgets = [
                w for w in available_widgets
                if not w.permissions_required
                or all(p in permissions for p in w.permissions_required)
            ]

        # 5. Build tabs from capabilities
        tabs = []
        for i, cap in enumerate(caps):
            for tab_name in cap.manifest.ui.tabs:
                widget_id = f"{cap.id}.{tab_name.lower().replace(' ', '_')}"
                tab_widgets = [w.id for w in available_widgets
                               if w.capability_id == cap.id
                               and tab_name.lower().replace(' ', '_') in w.id]
                if not tab_widgets:
                    # Use any widget from this capability
                    tab_widgets = [w.id for w in available_widgets
                                   if w.capability_id == cap.id]

                tabs.append(ViewerTab(
                    id=f"{cap.id}_{tab_name.lower().replace(' ', '_')}",
                    label=tab_name.replace("_", " ").title(),
                    widget_ids=tab_widgets,
                    icon=cap.manifest.ui.icon,
                    order=i,
                    default=(i == 0),
                ))

        # 6. Get user's saved layout (or use default)
        layout = self.ux.layout.get_layout(user_id, tenant_id, entity_type.value)
        default_layout = None
        if layout:
            default_layout = {
                zone: [w.id for w in zone_obj.widgets]
                for zone, zone_obj in layout.zones.items()
            }

        return ViewerConfig(
            entity_type=entity_type,
            entity_id=entity_id,
            tabs=tabs,
            available_widgets=available_widgets,
            default_layout=default_layout or self._default_layout_for(entity_type),
            context={
                "entity_type": entity_type.value,
                "entity_id": entity_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
            },
        )

    def _default_layout_for(self, entity_type: EntityType) -> dict:
        """Return the default layout template for an entity type."""
        if entity_type == EntityType.COMPANY:
            return {
                "top": [],
                "left": ["ai_copilot"],
                "center": ["overview", "timeline", "signals", "feature_scores"],
                "right": ["recommendations", "buying_committee", "revenue"],
                "bottom": [],
            }
        elif entity_type == EntityType.DEAL:
            return {
                "top": ["overview"],
                "left": ["ai_copilot"],
                "center": ["revenue", "timeline", "tasks"],
                "right": ["recommendations", "buying_committee"],
                "bottom": ["audit_log"],
            }
        elif entity_type == EntityType.CONTACT:
            return {
                "top": ["overview"],
                "left": [],
                "center": ["timeline", "emails", "meetings"],
                "right": ["ai_copilot"],
                "bottom": [],
            }
        return {
            "top": [],
            "left": ["ai_copilot"],
            "center": ["overview", "timeline"],
            "right": [],
            "bottom": [],
        }

    def render_config(self, config: ViewerConfig) -> dict:
        """Generate the complete render config for frontend consumption."""
        return config.to_dict()
