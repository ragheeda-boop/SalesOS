"""UX Runtime REST API — navigation, layout, widgets, commands, notifications, themes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runtime.ux_runtime import UXRuntime, NavItem, Notification, NotificationPriority

router = APIRouter(prefix="/api/v1/ux", tags=["Experience Layer"])

# Reference to the global UX runtime (set at startup)
ux_runtime: UXRuntime = None  # type: ignore


def set_ux_runtime(ux: UXRuntime):
    global ux_runtime
    ux_runtime = ux


# ── Navigation ────────────────────────────────────────────────

@router.get("/nav/sidebar")
async def get_sidebar():
    """Get sidebar navigation from Capability Registry."""
    from runtime.capability_framework import Capability
    capabilities = [c.manifest.to_dict() for c in Capability.all()]
    items = ux_runtime.navigation.build_sidebar(capabilities)
    return [item.to_dict() for item in items]


@router.get("/nav/breadcrumbs")
async def get_breadcrumbs(path: str):
    """Resolve breadcrumbs for a given path."""
    from runtime.capability_framework import Capability
    capabilities = [c.manifest.to_dict() for c in Capability.all()]
    return ux_runtime.navigation.get_breadcrumbs(path, capabilities)


# ── Layout ────────────────────────────────────────────────────

class AddWidgetRequest(BaseModel):
    widget_type: str
    capability_id: str
    zone: str = "center"
    size: str = "full"
    config: dict = {}


@router.get("/layout/{entity_type}")
async def get_layout(entity_type: str, user_id: str, tenant_id: str):
    """Get user's saved layout for an entity type."""
    layout = ux_runtime.layout.get_layout(user_id, tenant_id, entity_type)
    if not layout:
        return {"user_id": user_id, "entity_type": entity_type, "zones": {}}
    return layout.to_dict()


@router.post("/layout/{entity_type}/widgets")
async def add_widget_to_layout(entity_type: str, user_id: str, tenant_id: str, req: AddWidgetRequest):
    """Add a widget to the user's layout."""
    widget = ux_runtime.widget.create_instance(
        widget_type=req.widget_type,
        capability_id=req.capability_id,
        config=req.config,
        zone=req.zone,
        size=req.size,
    )
    layout = ux_runtime.layout.add_widget(user_id, tenant_id, entity_type, widget, req.zone)
    if not layout:
        raise HTTPException(400, f"Invalid zone: {req.zone}")
    return widget.to_dict()


@router.delete("/layout/{entity_type}/widgets/{widget_id}")
async def remove_widget_from_layout(entity_type: str, widget_id: str, user_id: str, tenant_id: str):
    """Remove a widget from the user's layout."""
    success = ux_runtime.layout.remove_widget(user_id, tenant_id, entity_type, widget_id)
    if not success:
        raise HTTPException(404, "Widget not found")
    return {"status": "removed"}


@router.post("/layout/{entity_type}/reorder")
async def reorder_widget(entity_type: str, user_id: str, tenant_id: str,
                         widget_id: str, zone: str, order: int):
    """Reorder a widget to a new zone/position."""
    success = ux_runtime.layout.reorder_widget(user_id, tenant_id, entity_type,
                                                widget_id, zone, order)
    if not success:
        raise HTTPException(400, "Failed to reorder widget")
    return {"status": "reordered"}


# ── Commands ──────────────────────────────────────────────────

@router.get("/commands")
async def list_commands(category: str | None = None, query: str | None = None,
                        context: str | None = None):
    """List available commands, optionally filtered."""
    if query:
        results = ux_runtime.command.search(query, context=context)
        return [c.to_dict() for c in results]
    cmds = ux_runtime.command.all_commands(category)
    return [c.to_dict() for c in cmds]


@router.post("/commands/{command_id}/execute")
async def execute_command(command_id: str):
    """Execute a command (returns action metadata, actual execution is frontend-side)."""
    cmd = ux_runtime.command.search(command_id)
    if not cmd:
        raise HTTPException(404, f"Command '{command_id}' not found")
    return {"command_id": command_id, "label": cmd[0].label, "action": "executed"}


# ── Notifications ─────────────────────────────────────────────

@router.get("/notifications/{user_id}")
async def get_notifications(user_id: str, unread_only: bool = False):
    """Get notifications for a user."""
    if unread_only:
        notifs = ux_runtime.notification.get_unread(user_id)
    else:
        notifs = ux_runtime.notification.get_all(user_id)
    return [n.to_dict() for n in notifs]


@router.get("/notifications/{user_id}/badge")
async def get_notification_badge(user_id: str):
    """Get unread notification count."""
    return {"count": ux_runtime.notification.badge_count(user_id)}


@router.post("/notifications/{user_id}/mark-read/{notification_id}")
async def mark_notification_read(user_id: str, notification_id: str):
    """Mark a notification as read."""
    ux_runtime.notification.mark_read(user_id, notification_id)
    return {"status": "read"}


@router.post("/notifications/{user_id}/mark-all-read")
async def mark_all_notifications_read(user_id: str):
    """Mark all notifications as read."""
    ux_runtime.notification.mark_all_read(user_id)
    return {"status": "all_read"}


# ── Theme ─────────────────────────────────────────────────────

@router.get("/theme")
async def get_theme(tenant_id: str | None = None, is_dark: bool = False):
    """Get theme tokens as CSS variables."""
    theme = ux_runtime.theme.get_theme(tenant_id, is_dark)
    return {
        "tokens": theme.to_dict(),
        "css": theme.generate_css_variables(),
    }


@router.get("/theme/css")
async def get_theme_css(tenant_id: str | None = None, is_dark: bool = False):
    """Get theme as CSS custom properties string."""
    return {"css": ux_runtime.theme.generate_css(tenant_id, is_dark)}


# ── Object Viewer ─────────────────────────────────────────────

@router.get("/viewer/{entity_type}/{entity_id}")
async def get_object_viewer(entity_type: str, entity_id: str,
                            user_id: str, tenant_id: str):
    """Get the complete viewer configuration for an entity."""
    from runtime.object_viewer import EntityType, UniversalObjectViewer
    from runtime.capability_framework import Capability

    try:
        etype = EntityType(entity_type)
    except ValueError:
        raise HTTPException(400, f"Invalid entity type: {entity_type}")

    viewer = UniversalObjectViewer(ux_runtime)
    config = viewer.get_viewer(etype, entity_id, user_id, tenant_id)
    return config.to_dict()
