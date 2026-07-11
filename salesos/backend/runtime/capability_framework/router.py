"""Capability Registry REST API — the single source of truth for what the platform can do.

Company360, Dynamic Navigation, Dynamic Search, Dynamic Permissions, AI — all read from here.
No capability is hardcoded anywhere; everything is discovered through this API.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import verify_token
from runtime.capability_framework import Capability, CapabilityStatus

router = APIRouter(prefix="/api/v1/capabilities", tags=["Capability Framework"], dependencies=[Depends(verify_token)])


class CapabilityResponse(BaseModel):
    id: str
    name: str
    version: str
    description: str
    owner: str
    status: str
    dependencies: list[str]
    contract: dict
    ui: dict
    health: dict
    tags: list[str]


@router.get("", response_model=list[CapabilityResponse])
async def list_capabilities(status: str | None = None, tag: str | None = None):
    """List all registered capabilities, optionally filtered by status or tag."""
    caps = Capability.all()
    if status:
        try:
            caps = [c for c in caps if c.manifest.status == CapabilityStatus(status)]
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    if tag:
        caps = [c for c in caps if tag in c.manifest.tags]
    return [CapabilityResponse(**c.manifest.to_dict()) for c in sorted(caps, key=lambda c: c.id)]


@router.get("/{capability_id}", response_model=CapabilityResponse)
async def get_capability(capability_id: str):
    """Get a capability by ID."""
    cap = Capability.get(capability_id)
    if not cap:
        raise HTTPException(404, f"Capability '{capability_id}' not found")
    return CapabilityResponse(**cap.manifest.to_dict())


@router.get("/{capability_id}/health", response_model=dict)
async def get_capability_health(capability_id: str):
    """Get health metrics for a capability."""
    cap = Capability.get(capability_id)
    if not cap:
        raise HTTPException(404, f"Capability '{capability_id}' not found")
    return cap.manifest.health.to_dict()


@router.get("/{capability_id}/tabs", response_model=list[dict])
async def get_capability_tabs(capability_id: str):
    """Get UI tabs for a capability (used to generate tabbed views)."""
    cap = Capability.get(capability_id)
    if not cap:
        raise HTTPException(404, f"Capability '{capability_id}' not found")
    return [{"id": tab, "name": tab.replace("_", " ").title()} for tab in cap.manifest.ui.tabs]


@router.get("/nav/sidebar", response_model=list[dict])
async def get_sidebar_nav():
    """Get sidebar navigation items (generated from capability registry)."""
    return Capability.sidebar_items()


@router.get("/search/entities", response_model=list[dict])
async def get_searchable_entities():
    """Get all searchable entity types (generated from capability registry)."""
    return Capability.searchable_entities()


@router.get("/search/apis", response_model=list[dict])
async def get_registered_apis():
    """Get all registered API routes (generated from capability registry)."""
    return Capability.registered_apis()


@router.get("/search/events", response_model=list[dict])
async def get_registered_events():
    """Get all registered event types (generated from capability registry)."""
    return Capability.registered_events()


@router.get("/search/permissions", response_model=list[str])
async def get_registered_permissions():
    """Get all registered permission keys (generated from capability registry)."""
    return Capability.registered_permissions()
