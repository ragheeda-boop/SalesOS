"""Admin Demo Mode endpoints — toggle demo mode on/off."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import require_role_dep
from app.modules.demo_mode import DemoModeService, get_demo_mode_service

router = APIRouter(prefix="/api/v1/admin/demo-mode", tags=["Admin"])


class DemoModeResponse(BaseModel):
    demo_mode: bool


@router.post("/toggle", response_model=DemoModeResponse)
async def toggle_demo_mode(
    demo_service: DemoModeService = Depends(get_demo_mode_service),
    _role=Depends(require_role_dep("admin")),
):
    """Toggle demo mode on/off. Admin only."""
    enabled = demo_service.toggle()
    return DemoModeResponse(demo_mode=enabled)


@router.get("/status", response_model=DemoModeResponse)
async def demo_mode_status(
    demo_service: DemoModeService = Depends(get_demo_mode_service),
    _role=Depends(require_role_dep("admin")),
):
    """Get current demo mode status."""
    return DemoModeResponse(demo_mode=demo_service.enabled)
