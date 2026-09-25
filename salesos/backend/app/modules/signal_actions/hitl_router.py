"""Human-in-the-Loop API endpoints.

Feedback: accept/reject/modify NBA
Outcomes: log call/email/meeting results
Follow-ups: view pending, complete
Work Queue: My Day view
Metrics: feedback acceptance rate, outcome conversion, time-to-action
"""
import logging
from datetime import UTC, datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_current_user_role,
    require_permission_dep,
)

_LEADERBOARD_ROLES = {"admin", "manager"}
from app.database import async_session
from sdk.permissions import PermissionAction
from app.modules.signal_actions.hitl_service import (
    FeedbackAnalyticsService,
    FeedbackService,
    FollowupService,
    OutcomeService,
    OutcomeOpportunityNotFound,
    WorkQueueService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hitl", tags=["Human-in-the-Loop"])

_fb_svc = FeedbackService(async_session)
_out_svc = OutcomeService(async_session)
_fu_svc = FollowupService(async_session)

# Observation pipeline — wired to HITL feedback
from app.modules.effectiveness import EffectivenessService
_eff_svc = EffectivenessService(async_session)
_wq_svc = WorkQueueService(async_session)
_analytics_svc = FeedbackAnalyticsService(async_session)


# ── Request models ──────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    action_id: str
    recommendation_id: str
    company_name: str
    seller_id: str = Field(
        default="",
        description="Deprecated client field; seller identity is taken from the access token.",
    )
    decision: str = Field(..., pattern="^(accepted|rejected|modified)$")
    reason_code: str = Field(default="", pattern="^(wrong_person|bad_timing|not_relevant|already_contacted|budget_constraint|other|$)")
    notes: str = ""
    original_action_type: str
    modified_action_type: str = ""
    modified_target_contact_id: str = ""


class OutcomeRequest(BaseModel):
    action_id: str
    company_name: str
    opportunity_id: str | None = Field(default=None, max_length=36)
    # Required (PO decision B7, report 99): a NULL key defeated the
    # (tenant_id, action_id, idempotency_key) dedup constraint (report 87).
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    seller_id: str = Field(
        default="",
        description="Deprecated client field; seller identity is taken from the access token.",
    )
    outcome_type: str = Field(..., pattern="^(connected|no_answer|left_voicemail|email_sent|meeting_set|positive|negative|neutral|proposal_sent)$")
    notes: str = ""
    contact_reached: str = ""
    duration_seconds: int | None = None
    followup_required: bool = False
    occurred_at: str | None = None


class FollowupCompleteRequest(BaseModel):
    outcome: str = "completed"


# ── Feedback endpoints ──────────────────────────────────────────

@router.post("/feedback", summary="Record seller feedback", description="Record seller feedback on an NBA recommendation (accepted, rejected, or modified).")
async def record_feedback(
    body: FeedbackRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    current_user_id: str = Depends(get_current_user_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.CREATE)),
):
    """Record seller feedback on an NBA recommendation."""
    fb = await _fb_svc.record(
        tenant_id=tenant_id,
        action_id=body.action_id,
        recommendation_id=body.recommendation_id,
        company_name=body.company_name,
        seller_id=current_user_id,
        decision=body.decision,
        original_action_type=body.original_action_type,
        reason_code=body.reason_code,
        notes=body.notes,
        modified_action_type=body.modified_action_type,
        modified_target_contact_id=body.modified_target_contact_id,
    )

    # ── Observation: record feedback in account_funnel ──
    try:
        await _eff_svc.record_feedback_event(tenant_id, body.company_name, body.decision)
    except Exception:
        logger.exception("observation_feedback_failed: company=%s", body.company_name)

    return fb.to_dict()


@router.get("/feedback/company/{company_name}", summary="Get company feedback", description="Get the feedback history for a specific company.")
async def get_company_feedback(
    company_name: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Get feedback history for a company."""
    feedback = await _fb_svc.get_by_company(tenant_id, company_name)
    return {"count": len(feedback), "feedback": [f.to_dict() for f in feedback]}


@router.get("/feedback/seller/{seller_id}", summary="Get seller feedback", description="Get the feedback history for a specific seller.")
async def get_seller_feedback(
    seller_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Get feedback history for a seller."""
    feedback = await _fb_svc.get_by_seller(tenant_id, seller_id)
    return {"count": len(feedback), "feedback": [f.to_dict() for f in feedback]}


# ── Outcome endpoints ───────────────────────────────────────────

@router.post("/outcomes", summary="Record an outcome", description="Record an action outcome (connected, meeting_set, proposal_sent, etc.) and auto-generate follow-up if needed.")
async def record_outcome(
    body: OutcomeRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    current_user_id: str = Depends(get_current_user_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.CREATE)),
):
    """Record an action outcome and auto-generate follow-up if needed."""
    occurred_at = datetime.fromisoformat(body.occurred_at) if body.occurred_at else None
    try:
        outcome = await _out_svc.record(
            tenant_id=tenant_id,
            action_id=body.action_id,
            company_name=body.company_name,
            seller_id=current_user_id,
            outcome_type=body.outcome_type,
            opportunity_id=body.opportunity_id,
            idempotency_key=body.idempotency_key,
            notes=body.notes,
            contact_reached=body.contact_reached,
            duration_seconds=body.duration_seconds,
            followup_required=body.followup_required,
            occurred_at=occurred_at,
        )
    except OutcomeOpportunityNotFound as exc:
        raise HTTPException(status_code=404, detail="Opportunity not found") from exc

    # Auto-generate follow-up
    followup = None if outcome.is_replay else await _fu_svc.generate(tenant_id, outcome)

    # ── Observation: record outcome in account_funnel ──
    try:
        outcome_to_event = {
            "connected": "connection",
            "meeting_set": "meeting",
            "proposal_sent": "proposal",
            "positive": "opportunity",
        }
        event_type = outcome_to_event.get(body.outcome_type)
        if event_type:
            await _eff_svc.record_event(
                tenant_id=tenant_id,
                company_name=body.company_name,
                event_type=event_type,
                action_id=body.action_id,
            )
        await _eff_svc.record_outcome_event(tenant_id, body.company_name, body.outcome_type)
    except Exception:
        logger.exception("observation_outcome_failed: company=%s", body.company_name)

    return {
        "outcome": outcome.to_dict(),
        "followup": followup.to_dict() if followup else None,
    }


@router.get("/outcomes/company/{company_name}", summary="Get company outcomes", description="Get the outcome history for a specific company.")
async def get_company_outcomes(
    company_name: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Get outcome history for a company."""
    outcomes = await _out_svc.get_by_company(tenant_id, company_name)
    return {"count": len(outcomes), "outcomes": [o.to_dict() for o in outcomes]}


# ── Follow-up endpoints ─────────────────────────────────────────

@router.get("/followups", summary="List pending follow-ups", description="List pending follow-ups for a seller, auto-generated from outcomes.")
async def list_followups(
    seller_id: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """List pending follow-ups for this seller."""
    followups = await _fu_svc.get_pending(tenant_id, seller_id)
    return {"count": len(followups), "followups": [f.to_dict() for f in followups]}


@router.post("/followups/{followup_id}/complete", summary="Complete a follow-up", description="Mark a follow-up as completed with an outcome status.")
async def complete_followup(
    followup_id: str,
    body: FollowupCompleteRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.UPDATE)),
):
    """Mark a follow-up as completed."""
    ok = await _fu_svc.complete(tenant_id, followup_id, body.outcome)
    if not ok:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return {"success": True}


# ── Work Queue (My Day) ─────────────────────────────────────────

@router.get("/my-day", summary="Get the current seller's daily work queue")
async def get_my_day_for_current_user(
    tenant_id: str = Depends(get_current_tenant_id),
    current_user_id: str = Depends(get_current_user_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Resolve the seller from the authenticated token, never a client path value."""
    return await _wq_svc.get_my_day(tenant_id, current_user_id)


@router.get("/my-day/{seller_id}", summary="Get seller daily work queue", description="Get the seller's daily work queue with prioritized tasks and follow-ups.")
async def get_my_day(
    seller_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Get the seller's daily work queue."""
    return await _wq_svc.get_my_day(tenant_id, seller_id)


# ── Feedback Metrics ────────────────────────────────────────────

@router.get("/metrics/{seller_id}", summary="Get seller feedback metrics", description="Get feedback acceptance rate, outcome conversion rate, and follow-up completion rate for a seller.")
async def get_feedback_metrics(
    seller_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Get feedback and outcome metrics for a seller."""
    from sqlalchemy import text as sa_text

    async with async_session() as session:
        await session.execute(
            sa_text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": tenant_id},
        )

        # Acceptance rate
        fb_rows = await session.execute(
            sa_text("""
                SELECT decision, COUNT(*) as cnt
                FROM nba_feedback
                WHERE seller_id = :s
                GROUP BY decision
            """),
            {"s": seller_id},
        )
        fb_by_decision = {r[0]: r[1] for r in fb_rows.fetchall()}
        total_fb = sum(fb_by_decision.values())
        acceptance_rate = (fb_by_decision.get("accepted", 0) / total_fb * 100) if total_fb > 0 else 0

        # Outcome conversion (meeting_set / connected / positive / proposal_sent)
        outcome_rows = await session.execute(
            sa_text("""
                SELECT outcome_type, COUNT(*) as cnt
                FROM action_outcomes
                WHERE seller_id = :s
                GROUP BY outcome_type
            """),
            {"s": seller_id},
        )
        outcome_by_type = {r[0]: r[1] for r in outcome_rows.fetchall()}
        total_outcomes = sum(outcome_by_type.values())
        positive_outcomes = sum(
            outcome_by_type.get(t, 0)
            for t in ("connected", "positive", "meeting_set", "proposal_sent")
        )
        conversion_rate = (positive_outcomes / total_outcomes * 100) if total_outcomes > 0 else 0

        # Follow-up completion rate
        fu_rows = await session.execute(
            sa_text("""
                SELECT status, COUNT(*) as cnt
                FROM sales_followups
                WHERE seller_id = :s
                GROUP BY status
            """),
            {"s": seller_id},
        )
        fu_by_status = {r[0]: r[1] for r in fu_rows.fetchall()}
        total_fu = sum(fu_by_status.values())
        fu_completion = (fu_by_status.get("completed", 0) / total_fu * 100) if total_fu > 0 else 0

        return {
            "seller_id": seller_id,
            "feedback": {
                "total": total_fb,
                "accepted": fb_by_decision.get("accepted", 0),
                "rejected": fb_by_decision.get("rejected", 0),
                "modified": fb_by_decision.get("modified", 0),
                "acceptance_rate": round(acceptance_rate, 1),
            },
            "outcomes": {
                "total": total_outcomes,
                "by_type": outcome_by_type,
                "positive_outcomes": positive_outcomes,
                "conversion_rate": round(conversion_rate, 1),
            },
            "followups": {
                "total": total_fu,
                "by_status": fu_by_status,
                "completion_rate": round(fu_completion, 1),
            },
        }


# ── Feedback Analytics Dashboard ────────────────────────────────

@router.get("/analytics", summary="Get feedback analytics dashboard", description="Get feedback analytics: acceptance rate, outcome conversion, time-to-action, and seller productivity.")
async def get_analytics(
    seller_id: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    current_user_id: str = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Feedback analytics dashboard: acceptance rate, outcome conversion, time-to-action, seller productivity.

    PO decision B6 (report 99): the per-seller leaderboard is for managers/admins.
    Everyone else sees only their own figures and cannot query another seller.
    """
    if role in _LEADERBOARD_ROLES:
        return await _analytics_svc.get_dashboard(tenant_id, seller_id)
    return await _analytics_svc.get_dashboard(tenant_id, current_user_id, leaderboard=False)
