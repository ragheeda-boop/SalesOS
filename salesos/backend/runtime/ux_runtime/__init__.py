"""UX Runtime — six runtimes powering the Experience Layer.

Navigation Runtime    — sidebar, breadcrumbs, route discovery from Capability Registry
Layout Runtime       — widget canvas, zones, drag-drop, per-user persistence
Widget Runtime       — widget lifecycle (load → render → destroy), state management
Theme Runtime        — design token resolution, tenant overrides, dark/light mode
Command Runtime      — Global Ctrl+K, action registry, command palette
Notification Runtime — in-app notifications, toast, badge counts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from design_tokens import DesignTheme, get_theme


# ═══════════════════════════════════════════════════════════════
# Navigation Runtime
# ═══════════════════════════════════════════════════════════════

@dataclass
class NavItem:
    id: str
    label: str
    label_ar: Optional[str] = None
    icon: Optional[str] = None
    path: Optional[str] = None
    children: list[NavItem] = field(default_factory=list)
    capability_id: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    badge: Optional[str] = None
    order: int = 0
    is_active: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "label_ar": self.label_ar or self.label,
            "icon": self.icon,
            "path": self.path,
            "children": [c.to_dict() for c in self.children],
            "capability_id": self.capability_id,
            "permissions": self.permissions,
            "badge": self.badge,
            "order": self.order,
            "is_active": self.is_active,
        }


class NavigationRuntime:
    """Generates navigation from Capability Registry + overrides."""

    def __init__(self):
        self._overrides: dict[str, list[NavItem]] = {}

    def build_sidebar(self, capabilities: list[dict]) -> list[NavItem]:
        """Build sidebar from capability registry data."""
        items = []
        for cap in capabilities:
            ui = cap.get("ui", {})
            if not ui.get("sidebar"):
                continue
            item = NavItem(
                id=cap["id"],
                label=cap["name"],
                icon=ui.get("icon"),
                path=ui.get("routes", [None])[0] if ui.get("routes") else None,
                capability_id=cap["id"],
                permissions=cap.get("contract", {}).get("permissions", []),
                order=len(items),
            )
            if ui.get("tabs"):
                item.children = [
                    NavItem(
                        id=f"{cap['id']}.{tab}",
                        label=tab.replace("_", " ").title(),
                        path=f"{item.path}/{tab.lower()}" if item.path else None,
                    )
                    for tab in ui["tabs"]
                ]
            items.append(item)
        return sorted(items, key=lambda x: x.order)

    def get_breadcrumbs(self, path: str, capabilities: list[dict]) -> list[dict]:
        """Resolve breadcrumbs for a given path."""
        crumbs = [{"label": "Home", "path": "/"}]
        for cap in capabilities:
            routes = cap.get("ui", {}).get("routes", [])
            for route in routes:
                if route and path.startswith(route):
                    crumbs.append({"label": cap["name"], "path": route})
                    remaining = path[len(route):].strip("/")
                    if remaining:
                        crumbs.append({
                            "label": remaining.replace("-", " ").title(),
                            "path": path,
                        })
                    return crumbs
        return crumbs


# ═══════════════════════════════════════════════════════════════
# Widget Runtime
# ═══════════════════════════════════════════════════════════════

class WidgetLifecycle(Enum):
    REGISTERED = "registered"
    LOADING = "loading"
    LOADED = "loaded"
    RENDERED = "rendered"
    ERROR = "error"
    DESTROYED = "destroyed"


@dataclass
class WidgetInstance:
    id: str
    widget_type: str
    capability_id: str
    config: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)
    lifecycle: WidgetLifecycle = WidgetLifecycle.REGISTERED
    zone: str = "center"
    order: int = 0
    size: str = "full"  # full, half, third, quarter
    visible: bool = True
    permissions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "widget_type": self.widget_type,
            "capability_id": self.capability_id,
            "config": self.config,
            "state": self.state,
            "lifecycle": self.lifecycle.value,
            "zone": self.zone,
            "order": self.order,
            "size": self.size,
            "visible": self.visible,
            "permissions": self.permissions,
        }


class WidgetRuntime:
    """Manages widget lifecycle across the application."""

    def __init__(self):
        self._instances: dict[str, WidgetInstance] = {}
        self._listeners: dict[str, list[Callable]] = {}

    def create_instance(self, widget_type: str, capability_id: str,
                        config: dict | None = None, zone: str = "center",
                        size: str = "full") -> WidgetInstance:
        import uuid
        inst = WidgetInstance(
            id=str(uuid.uuid4()),
            widget_type=widget_type,
            capability_id=capability_id,
            config=config or {},
            zone=zone,
            size=size,
        )
        self._instances[inst.id] = inst
        self._emit("widget.created", inst)
        return inst

    def get_instance(self, instance_id: str) -> Optional[WidgetInstance]:
        return self._instances.get(instance_id)

    def get_instances(self, capability_id: str) -> list[WidgetInstance]:
        return [w for w in self._instances.values()
                if w.capability_id == capability_id]

    def update_config(self, instance_id: str, config: dict):
        inst = self._instances.get(instance_id)
        if inst:
            inst.config.update(config)
            self._emit("widget.config_updated", inst)

    def destroy_instance(self, instance_id: str):
        inst = self._instances.pop(instance_id, None)
        if inst:
            inst.lifecycle = WidgetLifecycle.DESTROYED
            self._emit("widget.destroyed", inst)

    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)

    def _emit(self, event: str, widget: WidgetInstance):
        for cb in self._listeners.get(event, []):
            try:
                cb(widget)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# Layout Runtime
# ═══════════════════════════════════════════════════════════════

@dataclass
class LayoutZone:
    name: str  # left, right, center, top, bottom
    widgets: list[WidgetInstance] = field(default_factory=list)
    collapsed: bool = False
    width: Optional[str] = None  # e.g. "300px", "1fr"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "widgets": [w.to_dict() for w in sorted(self.widgets, key=lambda x: x.order)],
            "collapsed": self.collapsed,
            "width": self.width,
        }


@dataclass
class UserLayout:
    user_id: str
    tenant_id: str
    entity_type: str  # company, deal, contact, workspace
    zones: dict[str, LayoutZone] = field(default_factory=lambda: {
        "top": LayoutZone("top", []),
        "left": LayoutZone("left", [], width="320px"),
        "center": LayoutZone("center", []),
        "right": LayoutZone("right", [], width="320px"),
        "bottom": LayoutZone("bottom", []),
    })
    is_default: bool = False

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "entity_type": self.entity_type,
            "zones": {k: v.to_dict() for k, v in self.zones.items()},
            "is_default": self.is_default,
        }


class LayoutRuntime:
    """Per-user, per-entity-type layout persistence and resolution."""

    def __init__(self):
        self._layouts: dict[str, UserLayout] = {}

    def _key(self, user_id: str, tenant_id: str, entity_type: str) -> str:
        return f"{tenant_id}:{user_id}:{entity_type}"

    def get_or_create(self, user_id: str, tenant_id: str,
                      entity_type: str) -> UserLayout:
        key = self._key(user_id, tenant_id, entity_type)
        if key not in self._layouts:
            self._layouts[key] = UserLayout(
                user_id=user_id, tenant_id=tenant_id, entity_type=entity_type,
            )
        return self._layouts[key]

    def add_widget(self, user_id: str, tenant_id: str, entity_type: str,
                   widget: WidgetInstance, zone: str = "center") -> Optional[UserLayout]:
        layout = self.get_or_create(user_id, tenant_id, entity_type)
        if zone not in layout.zones:
            return None
        widget.zone = zone
        widget.order = len(layout.zones[zone].widgets)
        layout.zones[zone].widgets.append(widget)
        return layout

    def remove_widget(self, user_id: str, tenant_id: str, entity_type: str,
                      widget_id: str) -> bool:
        layout = self.get_or_create(user_id, tenant_id, entity_type)
        for zone in layout.zones.values():
            zone.widgets = [w for w in zone.widgets if w.id != widget_id]
        return True

    def reorder_widget(self, user_id: str, tenant_id: str, entity_type: str,
                       widget_id: str, new_zone: str, new_order: int) -> bool:
        layout = self.get_or_create(user_id, tenant_id, entity_type)
        widget = None
        for zone in layout.zones.values():
            for w in zone.widgets:
                if w.id == widget_id:
                    widget = w
                    zone.widgets = [x for x in zone.widgets if x.id != widget_id]
                    break
            if widget:
                break
        if not widget or new_zone not in layout.zones:
            return False
        widget.zone = new_zone
        layout.zones[new_zone].widgets.insert(new_order, widget)
        # Re-index orders
        for i, w in enumerate(layout.zones[new_zone].widgets):
            w.order = i
        return True

    def get_layout(self, user_id: str, tenant_id: str,
                   entity_type: str) -> Optional[UserLayout]:
        return self._layouts.get(self._key(user_id, tenant_id, entity_type))


# ═══════════════════════════════════════════════════════════════
# Theme Runtime
# ═══════════════════════════════════════════════════════════════

class ThemeRuntime:
    """Resolves Design Tokens per tenant, with dark/light mode."""

    def __init__(self):
        self._tenant_themes: dict[str, DesignTheme] = {}

    def get_theme(self, tenant_id: Optional[str] = None,
                  is_dark: bool = False) -> DesignTheme:
        base = get_theme("default")
        if tenant_id and tenant_id in self._tenant_themes:
            base = self._tenant_themes[tenant_id]
        if is_dark:
            dark = DesignTheme(name=f"{base.name}-dark", is_dark=True)
            dark.colors.surface = "#18181B"
            dark.colors.surface_secondary = "#27272A"
            dark.colors.surface_tertiary = "#3F3F46"
            dark.colors.border = "#3F3F46"
            dark.colors.border_strong = "#52525B"
            dark.colors.text_primary = "#FAFAFA"
            dark.colors.text_secondary = "#A1A1AA"
            dark.colors.text_tertiary = "#71717A"
            dark.colors.text_inverse = "#09090B"
            return dark
        return base

    def set_tenant_theme(self, tenant_id: str, theme: DesignTheme):
        self._tenant_themes[tenant_id] = theme

    def generate_css(self, tenant_id: Optional[str] = None,
                     is_dark: bool = False) -> str:
        return self.get_theme(tenant_id, is_dark).generate_css_variables()


# ═══════════════════════════════════════════════════════════════
# Command Runtime
# ═══════════════════════════════════════════════════════════════

@dataclass
class Command:
    id: str
    label: str
    label_ar: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    category: str = "general"  # general, navigation, creation, ai, workflow
    shortcut: Optional[str] = None  # e.g. "Ctrl+K", "C"
    handler: Optional[Callable] = None
    permissions: list[str] = field(default_factory=list)
    context: Optional[str] = None  # e.g. "company", "deal" — null for global

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "label_ar": self.label_ar or self.label,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "shortcut": self.shortcut,
            "permissions": self.permissions,
            "context": self.context,
        }


class CommandRuntime:
    """Global Command Bar (Ctrl+K) — action registry with context awareness."""

    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._register_defaults()

    def _register_defaults(self):
        defaults = [
            Command("create-company", "Create Company", category="creation",
                    shortcut="C", icon="building"),
            Command("search", "Search", description="Search across all entities",
                    category="navigation", shortcut="Ctrl+K", icon="search"),
            Command("open-dashboard", "Go to Dashboard", category="navigation",
                    shortcut="G D", icon="layout-dashboard"),
            Command("ask-ai", "Ask AI", description="Ask anything about your data",
                    category="ai", shortcut="Ctrl+Space", icon="sparkles"),
            Command("create-deal", "Create Deal", category="creation",
                    shortcut="D", icon="handshake"),
            Command("create-contact", "Create Contact", category="creation",
                    shortcut="Shift+C", icon="user-plus"),
            Command("create-workflow", "Create Workflow", category="creation",
                    icon="workflow"),
        ]
        for cmd in defaults:
            self.register(cmd)

    def register(self, command: Command):
        self._commands[command.id] = command

    def unregister(self, command_id: str):
        self._commands.pop(command_id, None)

    def search(self, query: str, context: Optional[str] = None,
               permissions: Optional[list[str]] = None) -> list[Command]:
        query = query.lower()
        results = []
        for cmd in self._commands.values():
            if context and cmd.context and cmd.context != context:
                continue
            if permissions and cmd.permissions:
                if not all(p in permissions for p in cmd.permissions):
                    continue
            if (query in cmd.label.lower()
                    or query in cmd.id.lower()
                    or (cmd.description and query in cmd.description.lower())):
                results.append(cmd)
        return results[:10]

    def execute(self, command_id: str, context: Optional[dict] = None) -> Any:
        cmd = self._commands.get(command_id)
        if cmd and cmd.handler:
            return cmd.handler(context or {})
        return None

    def all_commands(self, category: Optional[str] = None) -> list[Command]:
        if category:
            return [c for c in self._commands.values() if c.category == category]
        return list(self._commands.values())


# ═══════════════════════════════════════════════════════════════
# Notification Runtime
# ═══════════════════════════════════════════════════════════════

class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    id: str
    user_id: str
    tenant_id: str
    title: str
    title_ar: Optional[str] = None
    body: Optional[str] = None
    body_ar: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    category: str = "general"  # general, system, mention, signal, task, deal
    link: Optional[str] = None
    read: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "title_ar": self.title_ar or self.title,
            "body": self.body,
            "body_ar": self.body_ar or self.body,
            "priority": self.priority.value,
            "category": self.category,
            "link": self.link,
            "read": self.read,
            "created_at": self.created_at.isoformat(),
        }


class NotificationRuntime:
    """In-app notifications with priority, categories, and badge counts."""

    def __init__(self):
        self._notifications: dict[str, list[Notification]] = {}  # user_id → list

    def send(self, notification: Notification):
        self._notifications.setdefault(notification.user_id, []).append(notification)

    def get_unread(self, user_id: str) -> list[Notification]:
        return [n for n in self._notifications.get(user_id, []) if not n.read]

    def get_all(self, user_id: str, limit: int = 50) -> list[Notification]:
        notifs = self._notifications.get(user_id, [])
        return sorted(notifs, key=lambda x: x.created_at, reverse=True)[:limit]

    def mark_read(self, user_id: str, notification_id: str):
        for n in self._notifications.get(user_id, []):
            if n.id == notification_id:
                n.read = True
                break

    def mark_all_read(self, user_id: str):
        for n in self._notifications.get(user_id, []):
            n.read = True

    def badge_count(self, user_id: str) -> int:
        return len(self.get_unread(user_id))

    def get_by_category(self, user_id: str, category: str) -> list[Notification]:
        return [n for n in self._notifications.get(user_id, [])
                if n.category == category]


# ═══════════════════════════════════════════════════════════════
# UX Runtime — aggregates all sub-runtimes
# ═══════════════════════════════════════════════════════════════

@dataclass
class UXRuntime:
    navigation: NavigationRuntime = field(default_factory=NavigationRuntime)
    widget: WidgetRuntime = field(default_factory=WidgetRuntime)
    layout: LayoutRuntime = field(default_factory=LayoutRuntime)
    theme: ThemeRuntime = field(default_factory=ThemeRuntime)
    command: CommandRuntime = field(default_factory=CommandRuntime)
    notification: NotificationRuntime = field(default_factory=NotificationRuntime)

    def to_dict(self) -> dict:
        return {
            "navigation": {"status": "ready"},
            "widget": {"instances": len(self.widget._instances)},
            "layout": {"layouts": len(self.layout._layouts)},
            "theme": {"themes": ["default"]},
            "command": {"commands": len(self.command._commands)},
            "notification": {"status": "ready"},
        }
