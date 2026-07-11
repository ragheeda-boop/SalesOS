"""NBA REST API — endpoints for Next Best Action engine."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id
from runtime.nba_engine import NBAEngine

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_nba_response(nba) -> dict:
    """Convert NBAResult to response dict."""
    return {
        "id": nba.id,
        "opportunity_id": nba.opportunity_id,
        "action": nba.action,
        "reason": nba.reason,
        "confidence": max(0.0, min(1.0, nba.confidence)),
        "confidence_label": nba.confidence_label,
        "source": nba.source,
        "alternatives": [{"action": a.action, "reason": a.reason, "confidence": a.confidence} for a in nba.alternatives],
        "evidence": [{"type": e.type, "description": e.description, "source": e.source, "confidence": e.confidence} for e in nba.evidence],
        "potential_risks": [{"type": r.type, "level": r.level, "description": r.description} for r in nba.potential_risks],
        "status": nba.status,
        "created_at": nba.created_at,
        "updated_at": nba.updated_at,
    }


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
    nba_id: str = Field(max_length=100)
    action: str = Field(pattern="^(accepted|dismissed)$")
    reason: str | None = Field(None, max_length=1000)


@router.get("/opportunities/{opportunity_id}/nba", response_model=NBAResponse)
async def get_nba(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get the current Next Best Action for an opportunity."""
    try:
        engine = getattr(request.app.state, "nba_engine", None)
        if not engine:
            raise HTTPException(status_code=503, detail="NBA Engine not initialized")
        nba = await engine.get_or_compute(opportunity_id, tenant_id)
        if not nba:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return _to_nba_response(nba)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_nba failed for %s: %s", opportunity_id, exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/opportunities/{opportunity_id}/nba/refresh", response_model=NBAResponse)
async def refresh_nba(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Force recompute the Next Best Action for an opportunity."""
    try:
        engine = getattr(request.app.state, "nba_engine", None)
        if not engine:
            raise HTTPException(status_code=503, detail="NBA Engine not initialized")
        nba = await engine.recompute(opportunity_id, tenant_id)
        if not nba:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return _to_nba_response(nba)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("refresh_nba failed for %s: %s", opportunity_id, exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/opportunities/{opportunity_id}/nba/feedback")
async def record_nba_feedback(
    opportunity_id: str,
    body: NBAFeedbackRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Record user feedback on an NBA recommendation."""
    try:
        engine = getattr(request.app.state, "nba_engine", None)
        if not engine:
            raise HTTPException(status_code=503, detail="NBA Engine not initialized")
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="User identity required")
        await engine.record_feedback(
            opportunity_id=opportunity_id,
            nba_id=body.nba_id,
            user_id=user_id,
            action=body.action,
            reason=body.reason,
        )
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("record_nba_feedback failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
