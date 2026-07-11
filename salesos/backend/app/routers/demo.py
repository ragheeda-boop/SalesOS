"""Demo Environment API — reset, status, and scenario endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import require_role_dep, verify_token
from app.modules.demo_mode import DemoModeService, get_demo_mode_service

router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])


class DemoStatusResponse(BaseModel):
    demo_mode: bool
    demo_data_available: bool
    companies_count: int
    opportunities_count: int
    total_records: int


class ScenarioResponse(BaseModel):
    id: str
    title: str
    description: str
    steps: list[dict]


class ResetResponse(BaseModel):
    message: str
    companies: int
    opportunities: int
    meetings: int
    emails: int
    signals: int
    tasks: int
    nba_recommendations: int
    workflow_templates: int
    rag_documents: int
    analytics: int
    timeline_events: int


@router.get("/status", response_model=DemoStatusResponse)
async def demo_status(
    demo_service: DemoModeService = Depends(get_demo_mode_service),
):
    """Check current demo mode status."""
    status = demo_service.get_status()
    return DemoStatusResponse(
        demo_mode=status["demo_mode"],
        demo_data_available=status["demo_data_available"],
        companies_count=status["companies_count"],
        opportunities_count=status["opportunities_count"],
        total_records=status["total_records"],
    )


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(
    demo_service: DemoModeService = Depends(get_demo_mode_service),
    _auth=Depends(verify_token),
):
    """List available demo scenarios."""
    return demo_service.get_scenarios()


@router.post("/reset", response_model=ResetResponse)
async def reset_demo(
    demo_service: DemoModeService = Depends(get_demo_mode_service),
    _auth=Depends(verify_token),
    _role=Depends(require_role_dep("admin")),
):
    """Reset all demo data and re-seed. Only available when DEMO_MODE is enabled."""
    if not demo_service.enabled:
        raise HTTPException(status_code=403, detail="Demo mode is not enabled. Set DEMO_MODE=true to use this endpoint.")

    try:
        from backend.demo.reset import reset_demo_data
        data = reset_demo_data()
    except ImportError:
        try:
            from demo.reset import reset_demo_data
            data = reset_demo_data()
        except ImportError:
            raise HTTPException(status_code=500, detail="Demo reset module not found. Ensure backend.demo.reset is importable.")

    demo_service.reload_demo_data()

    return ResetResponse(
        message="Demo environment reset successfully",
        companies=data["total"]["companies"],
        opportunities=data["total"]["opportunities"],
        meetings=data["total"]["meetings"],
        emails=data["total"]["emails"],
        signals=data["total"]["signals"],
        tasks=data["total"]["tasks"],
        nba_recommendations=data["total"]["nba_recommendations"],
        workflow_templates=data["total"]["workflow_templates"],
        rag_documents=data["total"]["rag_documents"],
        analytics=data["total"]["dashboard_analytics"],
        timeline_events=data["total"]["timeline_events"],
    )
