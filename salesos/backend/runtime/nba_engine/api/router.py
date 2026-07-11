"""NBA REST API — endpoints for Next Best Action engine."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.dependencies import get_current_tenant_id
from runtime.nba_engine import NBAEngine

router = APIRouter()


class NBAResponse(BaseModel):
    id: str
    opportunity_id: str
    action: str
    reason: str
    confidence: float
    confidence_label: str
    source: str
    alternatives: list[dict] = []
    evidence: list[dict] = []
    potential_risks: list[dict] = []
    due_by: str | None = None
    status: str = "pending"
    created_at: str = ""
    updated_at: str = ""


class NBAFeedbackRequest(BaseModel):
    nba_id: str
    action: str  # accepted | dismissed
    reason: str | None = None


@router.get("/opportunities/{opportunity_id}/nba", response_model=NBAResponse)
async def get_nba(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get the current Next Best Action for an opportunity."""
    engine = getattr(request.app.state, "nba_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="NBA Engine not initialized")
    nba = await engine.get_or_compute(opportunity_id, tenant_id)
    if not nba:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return NBAResponse(
        id=nba.id,
        opportunity_id=nba.opportunity_id,
        action=nba.action,
        reason=nba.reason,
        confidence=nba.confidence,
        confidence_label=nba.confidence_label,
        source=nba.source,
        alternatives=[{"action": a.action, "reason": a.reason, "confidence": a.confidence} for a in nba.alternatives],
        evidence=[{"type": e.type, "description": e.description, "source": e.source, "confidence": e.confidence} for e in nba.evidence],
        potential_risks=[{"type": r.type, "level": r.level, "description": r.description} for r in nba.potential_risks],
        status=nba.status,
        created_at=nba.created_at,
        updated_at=nba.updated_at,
    )


@router.post("/opportunities/{opportunity_id}/nba/refresh", response_model=NBAResponse)
async def refresh_nba(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Force recompute the Next Best Action for an opportunity."""
    engine = getattr(request.app.state, "nba_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="NBA Engine not initialized")
    nba = await engine.recompute(opportunity_id, tenant_id)
    if not nba:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return NBAResponse(
        id=nba.id,
        opportunity_id=nba.opportunity_id,
        action=nba.action,
        reason=nba.reason,
        confidence=nba.confidence,
        confidence_label=nba.confidence_label,
        source=nba.source,
        alternatives=[{"action": a.action, "reason": a.reason, "confidence": a.confidence} for a in nba.alternatives],
        evidence=[{"type": e.type, "description": e.description, "source": e.source, "confidence": e.confidence} for e in nba.evidence],
        potential_risks=[{"type": r.type, "level": r.level, "description": r.description} for r in nba.potential_risks],
        status=nba.status,
        created_at=nba.created_at,
        updated_at=nba.updated_at,
    )


@router.post("/opportunities/{opportunity_id}/nba/feedback")
async def record_nba_feedback(
    opportunity_id: str,
    body: NBAFeedbackRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Record user feedback on an NBA recommendation."""
    engine = getattr(request.app.state, "nba_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="NBA Engine not initialized")
    await engine.record_feedback(
        opportunity_id=opportunity_id,
        nba_id=body.nba_id,
        user_id=request.state.user_id if hasattr(request.state, "user_id") else "system",
        action=body.action,
        reason=body.reason,
    )
    return {"status": "ok"}
