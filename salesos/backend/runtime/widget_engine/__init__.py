"""Widget Engine — the heart of composable experience.

Widgets are the atomic unit of UI in XP1. Every piece of UI is a Widget.
Tabs are Widgets. Dashboards are Widget containers. Company360 is a Viewer
that renders Widgets from the Capability Registry.

Widget
├── id, name, description, version
├── capability_id (links to Capability Registry)
├── permissions_required[]
├── apis_used[]
├── events_subscribed[]
├── configuration_schema (JSON Schema)
├── slots (zones the widget can occupy: left, right, center, top, bottom)
├── size_hints (min_w, min_h, default_w, default_h)
├── renderer (frontend component name)
└── tags[]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class WidgetSlot(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    FULL = "full"


@dataclass
class WidgetSizeHints:
    min_width: int = 2  # grid columns
    min_height: int = 1  # grid rows
    default_width: int = 4
    default_height: int = 2
    max_width: Optional[int] = None
    max_height: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "min_width": self.min_width,
            "min_height": self.min_height,
            "default_width": self.default_width,
            "default_height": self.default_height,
            "max_width": self.max_width,
            "max_height": self.max_height,
        }


@dataclass
class WidgetDefinition:
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    capability_id: str = ""
    permissions_required: list[str] = field(default_factory=list)
    apis_used: list[str] = field(default_factory=list)
    events_subscribed: list[str] = field(default_factory=list)
    configuration_schema: Optional[dict] = None  # JSON Schema
    slots: list[WidgetSlot] = field(default_factory=lambda: [WidgetSlot.CENTER])
    size_hints: WidgetSizeHints = field(default_factory=WidgetSizeHints)
    renderer: str = ""  # frontend component name, e.g. "TimelineWidget"
    tags: list[str] = field(default_factory=list)
    icon: Optional[str] = None
    ai_context: Optional[dict] = None  # what AI knows when this widget is active

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capability_id": self.capability_id,
            "permissions_required": self.permissions_required,
            "apis_used": self.apis_used,
            "events_subscribed": self.events_subscribed,
            "configuration_schema": self.configuration_schema,
            "slots": [s.value for s in self.slots],
            "size_hints": self.size_hints.to_dict(),
            "renderer": self.renderer,
            "tags": self.tags,
            "icon": self.icon,
            "ai_context": self.ai_context,
        }


# ── Widget Registry ───────────────────────────────────────────

class WidgetRegistry:
    """Central registry of all available widget types."""

    _widgets: dict[str, WidgetDefinition] = {}

    @classmethod
    def register(cls, widget: WidgetDefinition):
        cls._widgets[widget.id] = widget

    @classmethod
    def get(cls, widget_id: str) -> Optional[WidgetDefinition]:
        return cls._widgets.get(widget_id)

    @classmethod
    def all(cls) -> list[WidgetDefinition]:
        return list(cls._widgets.values())

    @classmethod
    def by_capability(cls, capability_id: str) -> list[WidgetDefinition]:
        return [w for w in cls._widgets.values()
                if w.capability_id == capability_id]

    @classmethod
    def by_slot(cls, slot: WidgetSlot) -> list[WidgetDefinition]:
        return [w for w in cls._widgets.values() if slot in w.slots]

    @classmethod
    def by_tag(cls, tag: str) -> list[WidgetDefinition]:
        return [w for w in cls._widgets.values() if tag in w.tags]

    @classmethod
    def generate_from_capabilities(cls) -> list[WidgetDefinition]:
        """Auto-generate widget definitions from the Capability Registry.

        Each capability with a UI tab definition becomes a widget.
        """
        from runtime.capability_framework import Capability
        generated = []
        for cap in Capability.all():
            ui = cap.manifest.ui
            if not ui.tabs:
                continue
            for tab in ui.tabs:
                widget_id = f"{cap.id}.{tab.lower().replace(' ', '_')}"
                if widget_id in cls._widgets:
                    continue
                w = WidgetDefinition(
                    id=widget_id,
                    name=tab.replace("_", " ").title(),
                    description=f"{tab} widget for {cap.manifest.name}",
                    capability_id=cap.id,
                    permissions_required=[
                        p for p in cap.manifest.contract.permissions
                        if "read" in p or "admin" in p
                    ],
                    apis_used=cap.manifest.contract.apis,
                    events_subscribed=cap.manifest.contract.events,
                    renderer=f"{cap.id.title().replace('-', '')}{tab.title().replace('_', '')}Widget",
                    icon=ui.icon,
                    tags=[cap.id, tab.lower(), "auto-generated"],
                    ai_context={"capability": cap.id, "entity_types": cap.manifest.contract.entities},
                )
                cls._widgets[widget_id] = w
                generated.append(w)
        return generated


# ── Built-In Widgets ──────────────────────────────────────────

def register_builtin_widgets():
    """Register all built-in widget types."""
    builtins = [
        WidgetDefinition(
            id="overview",
            name="Overview",
            description="Company overview with key metrics, status, and quick actions",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.TOP],
            size_hints=WidgetSizeHints(min_height=2, default_height=3, default_width=6),
            renderer="OverviewWidget",
            icon="layout-dashboard",
            ai_context={"summary": True, "key_metrics": True},
        ),
        WidgetDefinition(
            id="timeline",
            name="Timeline",
            description="Activity timeline for the entity",
            capability_id="timeline",
            slots=[WidgetSlot.CENTER, WidgetSlot.LEFT, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=3, default_height=6, default_width=4),
            renderer="TimelineWidget",
            icon="clock",
            events_subscribed=["*"],
            ai_context={"timeline": True, "recent_activity": True},
        ),
        WidgetDefinition(
            id="signals",
            name="Signals",
            description="Intent signals, buying signals, and triggers",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=3),
            renderer="SignalWidget",
            icon="activity",
            ai_context={"signals": True, "intent": True},
        ),
        WidgetDefinition(
            id="buying_committee",
            name="Buying Committee",
            description="Key decision makers and their roles",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.LEFT, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=3),
            renderer="BuyingCommitteeWidget",
            icon="users",
            ai_context={"contacts": True, "decision_makers": True},
        ),
        WidgetDefinition(
            id="revenue",
            name="Revenue",
            description="Revenue metrics, deals, and pipeline",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT, WidgetSlot.TOP],
            size_hints=WidgetSizeHints(min_height=2, default_height=3, default_width=4),
            renderer="RevenueWidget",
            icon="trending-up",
            ai_context={"revenue": True, "deals": True, "pipeline": True},
        ),
        WidgetDefinition(
            id="knowledge_graph_view",
            name="Graph",
            description="Entity relationship graph visualization",
            capability_id="knowledge-graph",
            slots=[WidgetSlot.CENTER, WidgetSlot.FULL],
            size_hints=WidgetSizeHints(min_height=4, default_height=6, default_width=6),
            renderer="GraphWidget",
            icon="share2",
            ai_context={"graph": True, "relationships": True},
        ),
        WidgetDefinition(
            id="company_products",
            name="Products",
            description="Products and services offered",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=3, default_width=3),
            renderer="ProductsWidget",
            icon="package",
        ),
        WidgetDefinition(
            id="company_branches",
            name="Branches",
            description="Company branches and locations",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=3, default_width=3),
            renderer="BranchesWidget",
            icon="map-pin",
        ),
        WidgetDefinition(
            id="company_licenses",
            name="Licenses",
            description="Commercial licenses and permits",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=3, default_width=3),
            renderer="LicensesWidget",
            icon="file-text",
        ),
        WidgetDefinition(
            id="documents",
            name="Documents",
            description="Documents and files related to the entity",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=4),
            renderer="DocumentsWidget",
            icon="file",
        ),
        WidgetDefinition(
            id="meetings",
            name="Meetings",
            description="Meeting history and upcoming meetings",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=3),
            renderer="MeetingsWidget",
            icon="calendar",
            ai_context={"meetings": True, "calendar": True},
        ),
        WidgetDefinition(
            id="emails",
            name="Emails",
            description="Email history with the entity",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=3),
            renderer="EmailsWidget",
            icon="mail",
            ai_context={"emails": True},
        ),
        WidgetDefinition(
            id="recommendations",
            name="Recommendations",
            description="AI-powered next best actions and recommendations",
            capability_id="decision-engine",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT, WidgetSlot.TOP],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=3),
            renderer="RecommendationWidget",
            icon="zap",
            ai_context={"recommendations": True, "next_best_action": True},
        ),
        WidgetDefinition(
            id="tasks",
            name="Tasks",
            description="Tasks related to the entity",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.LEFT, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=3),
            renderer="TasksWidget",
            icon="check-square",
        ),
        WidgetDefinition(
            id="ai_copilot",
            name="AI Copilot",
            description="Context-aware AI assistant",
            capability_id="decision-engine",
            slots=[WidgetSlot.LEFT, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=4, default_height=8, default_width=3),
            renderer="AICopilotWidget",
            icon="sparkles",
            ai_context={"full_context": True},
        ),
        WidgetDefinition(
            id="audit_log",
            name="Audit",
            description="Audit trail of changes to the entity",
            capability_id="identity",
            slots=[WidgetSlot.BOTTOM, WidgetSlot.CENTER],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=6),
            renderer="AuditWidget",
            icon="clipboard-list",
        ),
        WidgetDefinition(
            id="entity_settings",
            name="Settings",
            description="Entity settings and configuration",
            capability_id="company",
            slots=[WidgetSlot.CENTER],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=4),
            renderer="SettingsWidget",
            icon="settings",
        ),
        WidgetDefinition(
            id="feature_scores",
            name="Scores",
            description="AI feature scores: ICP, Funding, Hiring, Growth, etc.",
            capability_id="feature-store",
            slots=[WidgetSlot.CENTER, WidgetSlot.TOP, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=3, default_width=4),
            renderer="FeatureScoreWidget",
            icon="bar-chart",
            ai_context={"features": True, "scores": True},
        ),
        WidgetDefinition(
            id="company_contacts",
            name="Contacts",
            description="Contacts associated with the company",
            capability_id="company",
            slots=[WidgetSlot.CENTER, WidgetSlot.RIGHT],
            size_hints=WidgetSizeHints(min_height=2, default_height=4, default_width=4),
            renderer="ContactsWidget",
            icon="user",
        ),
    ]
    for w in builtins:
        WidgetRegistry.register(w)
