"""Plugin Sandbox REST API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/plugins", tags=["Plugin Sandbox"])


class InstallRequest(BaseModel):
    plugin_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    permissions: list[str] = []
    hooks: list[str] = []
    config: dict = {}


@router.get("")
async def list_plugins():
    """List all installed plugins."""
    from app.main import app
    plugins = app.state.plugin_sandbox.list()
    return [p.to_dict() for p in plugins]


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Get plugin details."""
    from app.main import app
    plugin = app.state.plugin_sandbox.get(plugin_id)
    if not plugin:
        raise HTTPException(404, "Plugin not found")
    return plugin.to_dict()


@router.post("/install")
async def install_plugin(req: InstallRequest):
    """Install a new plugin."""
    from sdk.plugin_sdk import PluginManifest
    from app.main import app

    manifest = PluginManifest(
        id=req.plugin_id,
        name=req.name,
        version=req.version,
        description=req.description,
        author=req.author,
        permissions=req.permissions,
        hooks=req.hooks,
    )
    instance = app.state.plugin_sandbox.install(manifest, req.config)
    return instance.to_dict()


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    """Enable a plugin."""
    from app.main import app
    app.state.plugin_sandbox.enable(plugin_id)
    return {"status": "enabled"}


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    """Disable a plugin."""
    from app.main import app
    app.state.plugin_sandbox.disable(plugin_id)
    return {"status": "disabled"}


@router.delete("/{plugin_id}")
async def uninstall_plugin(plugin_id: str):
    """Uninstall a plugin."""
    from app.main import app
    app.state.plugin_sandbox.uninstall(plugin_id)
    return {"status": "uninstalled"}
