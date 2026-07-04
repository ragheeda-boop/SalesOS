"""Extension API REST API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/extensions", tags=["Extension API"])


@router.get("/hooks")
async def list_hooks():
    """List all registered hook points and their handlers."""
    from runtime.extension_api import HookRegistry
    return {
        "hooks": HookRegistry.hook_names(),
        "handlers": [h.to_dict() for h in HookRegistry.get_hooks()],
        "plugins": [p.to_dict() for p in HookRegistry.get_plugins()],
    }


@router.get("/hooks/{hook_name}")
async def get_hook(hook_name: str):
    """Get details for a specific hook."""
    from runtime.extension_api import HookRegistry
    handlers = HookRegistry.get_hooks(hook_name)
    if not handlers:
        raise HTTPException(404, f"Hook '{hook_name}' not found")
    return {"hook_name": hook_name, "handlers": [h.to_dict() for h in handlers]}
