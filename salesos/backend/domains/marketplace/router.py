"""Marketplace REST API — plugin install, uninstall, lifecycle, and configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.dependencies import verify_token

router = APIRouter(
    prefix="/api/v1/marketplace",
    tags=["Marketplace"],
    dependencies=[Depends(verify_token)],
)


# ── Request/Response Schemas ──────────────────────────────────

class InstallRequest(BaseModel):
    manifest: dict
    config: dict = {}


class UpdateConfigRequest(BaseModel):
    config: dict


class ApprovePermissionsRequest(BaseModel):
    permissions: list[str]


class PluginListResponse(BaseModel):
    plugins: list[dict]
    total: int


class PluginDetailResponse(BaseModel):
    plugin: dict
    state: str | None
    permissions_approved: list[str]


class LifecycleHistoryResponse(BaseModel):
    events: list[dict]
    total: int


# ── Helper ────────────────────────────────────────────────────

def _get_registry():
    from app.main import app
    from domains.marketplace.registry import PluginRegistry

    if not hasattr(app.state, "marketplace_registry"):
        app.state.marketplace_registry = PluginRegistry()
    return app.state.marketplace_registry


def _get_permission_gate():
    from app.main import app
    from domains.marketplace.sandbox import PermissionGate

    if not hasattr(app.state, "marketplace_permission_gate"):
        app.state.marketplace_permission_gate = PermissionGate()
    return app.state.marketplace_permission_gate


# ── Endpoints ─────────────────────────────────────────────────

@router.get("")
async def list_plugins(
    state: str | None = Query(None, description="Filter by state: active, disabled, installed"),
):
    """List all installed plugins, optionally filtered by state."""
    registry = _get_registry()
    lifecycle = registry.lifecycle
    plugins = registry.list()

    result = []
    for p in plugins:
        ps = lifecycle.get_state(p.plugin_id)
        if state and (ps is None or ps.value != state):
            continue
        d = p.to_dict()
        d["state"] = ps.value if ps else "unknown"
        result.append(d)

    return PluginListResponse(plugins=result, total=len(result))


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Get plugin details including state and approved permissions."""
    registry = _get_registry()
    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(404, "Plugin not found")

    lifecycle = registry.lifecycle
    gate = _get_permission_gate()
    state = lifecycle.get_state(plugin_id)

    return PluginDetailResponse(
        plugin=plugin.to_dict(),
        state=state.value if state else None,
        permissions_approved=gate.list_approved(plugin_id),
    )


@router.post("/install")
async def install_plugin(req: InstallRequest):
    """Install a new plugin with manifest validation."""
    registry = _get_registry()

    try:
        plugin = registry.install(req.manifest, req.config)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return PluginDetailResponse(
        plugin=plugin.to_dict(),
        state="active",
        permissions_approved=[],
    )


@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin(plugin_id: str):
    """Uninstall a plugin."""
    registry = _get_registry()

    try:
        registry.uninstall(plugin_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

    return {"status": "uninstalled", "plugin_id": plugin_id}


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    """Enable a disabled plugin."""
    registry = _get_registry()
    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(404, "Plugin not found")

    try:
        registry.activate(plugin_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"status": "enabled", "plugin_id": plugin_id}


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    """Disable an active plugin."""
    registry = _get_registry()
    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(404, "Plugin not found")

    try:
        registry.disable(plugin_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"status": "disabled", "plugin_id": plugin_id}


@router.get("/{plugin_id}/history")
async def get_lifecycle_history(plugin_id: str):
    """Get lifecycle history for a plugin."""
    registry = _get_registry()
    events = registry.lifecycle.history(plugin_id)
    return LifecycleHistoryResponse(
        events=[e.to_dict() for e in events],
        total=len(events),
    )


@router.post("/{plugin_id}/config")
async def update_plugin_config(plugin_id: str, req: UpdateConfigRequest):
    """Update plugin configuration."""
    registry = _get_registry()

    try:
        plugin = registry.update_config(plugin_id, req.config)
    except ValueError as e:
        raise HTTPException(404, str(e))

    return plugin.to_dict()


@router.get("/{plugin_id}/config")
async def get_plugin_config(plugin_id: str):
    """Get plugin configuration."""
    registry = _get_registry()
    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(404, "Plugin not found")
    return {"config": plugin.config}


@router.post("/{plugin_id}/permissions/approve")
async def approve_permissions(plugin_id: str, req: ApprovePermissionsRequest):
    """Approve specific permissions for a plugin."""
    gate = _get_permission_gate()
    gate.approve(plugin_id, req.permissions)
    return {"status": "approved", "permissions": gate.list_approved(plugin_id)}


@router.delete("/{plugin_id}/permissions/{permission}")
async def revoke_permission(plugin_id: str, permission: str):
    """Revoke a specific permission."""
    gate = _get_permission_gate()
    gate.revoke(plugin_id, permission)
    return {"status": "revoked", "permissions": gate.list_approved(plugin_id)}


@router.get("/{plugin_id}/permissions")
async def list_approved_permissions(plugin_id: str):
    """List all approved permissions for a plugin."""
    gate = _get_permission_gate()
    return {"plugin_id": plugin_id, "approved": gate.list_approved(plugin_id)}
