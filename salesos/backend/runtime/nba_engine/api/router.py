"""NBA REST API — endpoints for Next Best Action engine."""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import apply_tenant_guc, async_session
from app.dependencies import get_current_tenant_id, get_current_user_id, require_permission_dep
from app.modules.signal_actions.hitl_service import FeedbackService
from app.common.cache import cached, make_cache_key
from app.common.rate_limit import rate_limit_dep
from app.common.redis_client import AsyncRedisClient
from sdk.permissions import PermissionAction
from runtime.nba_engine import NBAEngine

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(rate_limit_dep("nba", 30, 60))]
)


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
    nba_id: uuid.UUID
    action: str = Field(pattern="^(accepted|dismissed)$")
    original_action_type: str = Field(min_length=1, max_length=50)
    reason: str | None = Field(None, max_length=1000)


_FEEDBACK_DECISION = {"accepted": "accepted", "dismissed": "rejected"}


@router.get("/opportunities/{opportunity_id}/nba", response_model=NBAResponse)
@cached("nba:recommendations", ttl=120)
async def get_nba(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("nba", PermissionAction.READ)),
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
    _rbac: None = Depends(require_permission_dep("nba", PermissionAction.CREATE)),
):
    """Force recompute the Next Best Action for an opportunity."""
    try:
        engine = getattr(request.app.state, "nba_engine", None)
        if not engine:
            raise HTTPException(status_code=503, detail="NBA Engine not initialized")
        nba = await engine.recompute(opportunity_id, tenant_id)
        if not nba:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        _redis = AsyncRedisClient()
        stale_key = make_cache_key(tenant_id, "nba:recommendations", {
            "opportunity_id": opportunity_id,
            "tenant_id": tenant_id,
        })
        await _redis.delete(stale_key)
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
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    _rbac: None = Depends(require_permission_dep("nba", PermissionAction.UPDATE)),
):
    """Record feedback through the single HITL feedback path (PO decision B4, report 99).

    Opportunity-level recommendations are not persisted sales actions, so the
    recommendation id is recorded as both action_id and recommendation_id.
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="User identity required")
    async with async_session() as session:
        await apply_tenant_guc(session, tenant_id)
        company_name = (await session.execute(
            text("""
                SELECT COALESCE(NULLIF(c.name_en, ''), c.name_ar, o.name)
                FROM commercial_opportunities o
                LEFT JOIN companies c ON c.id::text = o.company_id
                WHERE o.id = :oid AND o.tenant_id = :tid
            """),
            {"oid": opportunity_id, "tid": tenant_id},
        )).scalar_one_or_none()
    if company_name is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    fb = await FeedbackService(async_session).record(
        tenant_id=tenant_id,
        action_id=str(body.nba_id),
        recommendation_id=str(body.nba_id),
        company_name=company_name,
        seller_id=user_id,
        decision=_FEEDBACK_DECISION[body.action],
        original_action_type=body.original_action_type,
        notes=body.reason or "",
    )
    return {"status": "ok", "feedback_id": fb.id}
