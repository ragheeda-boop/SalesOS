"""Signal Actions REST API — Signal-driven Sales Actions.

Flow: Evidence -> Signals -> Qualification -> Priority -> NBA -> Sales Action
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

import logging

from app.database import async_session
from app.dependencies import get_current_tenant_id, require_permission_dep
from sdk.permissions import PermissionAction

logger = logging.getLogger(__name__)

from .actions import ActionExecutor
from .models import ActionType, SignalPriority
from .nba import generate_nba
from .priority import score_account
from .qualification import qualify_signal

# Observation pipeline — wired to real signal→action→outcome flow
from app.modules.effectiveness import EffectivenessService

router = APIRouter(prefix="/api/v1/signal-actions", tags=["Signal Actions"])

_executor = ActionExecutor(async_session)
_eff_svc = EffectivenessService(async_session)


# ── Request Models ───────────────────────────────────────────────


class QualifyRequest(BaseModel):
    company_name: str = Field(..., max_length=500)
    signal_type: str = Field(..., max_length=50)
    raw_confidence: str = Field(..., max_length=20)
    source_count: int = Field(default=1, ge=1)


class QualifyBatchRequest(BaseModel):
    signals: list[QualifyRequest]


class ScoreRequest(BaseModel):
    company_name: str = Field(..., max_length=500)
    crm_data: dict | None = None


class ExecuteRequest(BaseModel):
    nba_id: str = Field(..., max_length=36)
    company_name: str = Field(..., max_length=500)
    action_type: str = Field(..., max_length=50)
    urgency: str = Field(..., max_length=20)
    title: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=2000)
    rationale: str = Field(default="", max_length=2000)
    signal_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    channel: str = Field(default="", max_length=50)
    suggested_message: str = Field(default="", max_length=5000)


class CompleteRequest(BaseModel):
    action_id: str = Field(..., max_length=36)
    outcome: str = Field(default="neutral", pattern="^(positive|neutral|negative)$")
    notes: str = Field(default="", max_length=2000)


# ── Endpoints ────────────────────────────────────────────────────


@router.post("/qualify")
async def qualify_signal_endpoint(
    body: QualifyRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Qualify a single signal and return priority score."""
    from datetime import UTC, datetime

    qual = qualify_signal(
        signal_id="",
        company_name=body.company_name,
        signal_type=body.signal_type,
        raw_confidence=body.raw_confidence,
        detected_at=datetime.now(UTC),
        source_count=body.source_count,
    )
    return {"success": True, "qualification": qual.to_dict()}


@router.post("/qualify-batch")
async def qualify_batch(
    body: QualifyBatchRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Qualify multiple signals at once."""
    from datetime import UTC, datetime

    quals = []
    for s in body.signals:
        q = qualify_signal(
            signal_id="",
            company_name=s.company_name,
            signal_type=s.signal_type,
            raw_confidence=s.raw_confidence,
            detected_at=datetime.now(UTC),
            source_count=s.source_count,
        )
        quals.append(q.to_dict())
    return {"success": True, "count": len(quals), "qualifications": quals}


@router.post("/score")
async def score_account_endpoint(
    body: ScoreRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Score an account (intent + priority + recommended action)."""
    # Fetch signals from Agent Reach
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": tenant_id},
        )
        rows = await session.execute(
            text("SELECT * FROM agent_signals WHERE company_name = :c ORDER BY detected_at DESC"),
            {"c": body.company_name},
        )
        signals = rows.fetchall()

    # Qualify each signal
    from datetime import UTC, datetime

    quals = []
    for sig in signals:
        q = qualify_signal(
            signal_id=str(sig.id),
            company_name=sig.company_name,
            signal_type=sig.signal_type,
            raw_confidence=sig.confidence,
            detected_at=sig.detected_at,
        )
        quals.append(q)

    # Score account
    priority = score_account(
        company_name=body.company_name,
        tenant_id=tenant_id,
        qualifications=quals,
        crm_data=body.crm_data,
    )

    # Generate NBA
    nba = generate_nba(priority, quals)

    # ── Observation: upsert account_funnel ──
    try:
        signal_types = list({q.signal_type for q in quals})
        await _eff_svc.upsert_account(
            tenant_id=tenant_id,
            company_name=body.company_name,
            seller_id="",
            intent_score=priority.intent_score,
            intent_level=priority.intent_level.value,
            signal_types=signal_types,
            signal_count=len(quals),
            critical_signal_count=sum(1 for q in quals if q.signal_type in ("funding", "acquisition", "layoffs")),
            source_diversity=len(set(q.signal_type for q in quals)),
            nba_type=nba.action_type.value if nba.action_type else "",
            nba_urgency=nba.urgency.value if nba.urgency else "",
        )
    except Exception:
        logger.exception("observation_upsert_failed: %s", body.company_name)

    return {
        "success": True,
        "priority": priority.to_dict(),
        "nba": nba.to_dict(),
        "qualifications": [q.to_dict() for q in quals],
    }


@router.post("/execute")
async def execute_action(
    body: ExecuteRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.CREATE)),
):
    """Execute a sales action (persist audit trail)."""
    from datetime import UTC, datetime

    from .models import ActionType as AT, ActionUrgency as AU, NextBestAction

    nba = NextBestAction(
        id=body.nba_id,
        company_name=body.company_name,
        tenant_id=tenant_id,
        action_type=AT(body.action_type),
        urgency=AU(body.urgency),
        title=body.title,
        description=body.description,
        rationale=body.rationale,
        signal_ids=body.signal_ids,
        confidence=body.confidence,
        channel=body.channel,
        suggested_message=body.suggested_message,
    )
    action = await _executor.execute(nba, tenant_id)

    # ── Observation: record first_action in account_funnel ──
    try:
        await _eff_svc.record_event(
            tenant_id=tenant_id,
            company_name=body.company_name,
            event_type="first_action",
            action_id=action.id,
            action_type=body.action_type,
        )
        await _eff_svc.record_action_event(tenant_id, body.company_name)
    except Exception:
        logger.exception("observation_first_action_failed: %s", body.company_name)

    return {"success": True, "action": action.to_dict()}


@router.post("/complete")
async def complete_action(
    body: CompleteRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.UPDATE)),
):
    """Mark an action as completed."""
    try:
        ok = await _executor.complete(body.action_id, tenant_id, body.outcome, body.notes)
    except ValueError:
        raise HTTPException(status_code=404, detail="Action not found or not authorized")
    if not ok:
        raise HTTPException(status_code=404, detail="Action not found")

    # ── Observation: record outcome in account_funnel ──
    try:
        # Look up company_name from the action
        async with async_session() as sess:
            await sess.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id})
            r = await sess.execute(text("SELECT company_name FROM agent_sales_actions WHERE id = :id AND tenant_id = :t"), {"id": body.action_id, "t": tenant_id})
            row = r.fetchone()
            company_name = row[0] if row else ""

        if company_name:
            # Map outcome to funnel event
            outcome_to_event = {
                "connected": "connection",
                "meeting_set": "meeting",
                "proposal_sent": "proposal",
                "positive": "opportunity",
            }
            event_type = outcome_to_event.get(body.outcome)
            if event_type:
                await _eff_svc.record_event(
                    tenant_id=tenant_id,
                    company_name=company_name,
                    event_type=event_type,
                    action_id=body.action_id,
                )
            await _eff_svc.record_outcome_event(tenant_id, company_name, body.outcome)
    except Exception:
        logger.exception("observation_outcome_failed: action=%s", body.action_id)

    return {"success": True}


@router.get("/actions")
async def list_actions(
    company: str | None = None,
    status: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """List sales actions for this tenant."""
    actions = await _executor.get_actions(tenant_id, company, status)
    return {
        "count": len(actions),
        "actions": [a.to_dict() for a in actions],
    }


@router.get("/dashboard")
async def dashboard(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Get dashboard metrics: priority accounts, pending actions, signal breakdown."""
    pending = await _executor.get_pending_count(tenant_id)
    completed = await _executor.get_completed_count(tenant_id)

    # Count accounts with signals
    async with async_session() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": tenant_id},
        )
        rows = await session.execute(
            text("SELECT COUNT(DISTINCT company_name) FROM agent_signals")
        )
        accounts_with_signals = rows.scalar() or 0

        # Priority breakdown
        rows = await session.execute(
            text("""
                SELECT intent_level, COUNT(*) as cnt
                FROM agent_account_priorities
                GROUP BY intent_level
            """)
        )
        priority_breakdown = {r[0]: r[1] for r in rows}

        # Signal type breakdown
        rows = await session.execute(
            text("""
                SELECT signal_type, COUNT(*) as cnt
                FROM agent_signals
                GROUP BY signal_type
                ORDER BY cnt DESC
                LIMIT 10
            """)
        )
        signal_breakdown = [{"type": r[0], "count": r[1]} for r in rows]

    return {
        "accounts_with_signals": accounts_with_signals,
        "critical_accounts": priority_breakdown.get("very_high", 0) + priority_breakdown.get("high", 0),
        "pending_actions": pending,
        "completed_actions": completed,
        "priority_breakdown": priority_breakdown,
        "signal_breakdown": signal_breakdown,
    }
