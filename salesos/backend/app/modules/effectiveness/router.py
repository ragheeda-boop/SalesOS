"""Business Effectiveness API endpoints — observation, cohorts, lift, monotonicity, calibration."""
import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.dependencies import get_current_tenant_id, require_permission_dep
from app.database import async_session
from sdk.permissions import PermissionAction
from app.modules.effectiveness import EffectivenessService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/effectiveness", tags=["Business Effectiveness"])

_svc = EffectivenessService(async_session)


class AccountUpsertRequest(BaseModel):
    company_name: str
    seller_id: str
    intent_score: float = Field(ge=0, le=100)
    intent_level: str = ""
    sector: str = ""
    company_size: str = ""
    signal_types: list[str] = []
    signal_count: int = 0
    critical_signal_count: int = 0
    source_diversity: int = 0
    nba_type: str = ""
    nba_urgency: str = ""
    original_nba_type: str = ""
    seller_selected_action: str = ""


class FunnelEventRequest(BaseModel):
    company_name: str
    event_type: str = Field(..., pattern="^(first_action|connection|meeting|opportunity|proposal|won|lost)$")
    action_id: str = ""
    action_type: str = ""
    deal_value: float | None = None
    revenue: float | None = None


@router.get("/dashboard", summary="Get effectiveness dashboard", description="Full effectiveness dashboard with cohorts, lift, monotonicity, NBA effectiveness, and calibration readiness.")
async def get_dashboard(
    seller_id: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Full effectiveness dashboard with cohorts, lift, monotonicity, NBA effectiveness, calibration readiness."""
    return await _svc.get_dashboard(tenant_id, seller_id)


@router.get("/calibration-readiness", summary="Get calibration readiness", description="Calibration readiness assessment: status, checks passed/failed, model version.")
async def get_calibration_readiness(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Calibration readiness assessment only."""
    d = await _svc.get_dashboard(tenant_id)
    return {
        "status": d["calibration_readiness"]["status"],
        "checks": d["calibration_readiness"]["checks"],
        "passed": d["calibration_readiness"]["passed"],
        "total": d["calibration_readiness"]["total"],
        "failed_checks": d["calibration_readiness"]["failed_checks"],
        "model_version": d["model_version"],
    }


@router.get("/monotonicity", summary="Get monotonicity test results", description="Get monotonicity test results for the scoring model.")
async def get_monotonicity(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Monotonicity test results."""
    d = await _svc.get_dashboard(tenant_id)
    return d["monotonicity"]


@router.get("/segmentation", summary="Get dimensional segmentation", description="Get dimensional segmentation analysis across cohorts and attributes.")
async def get_segmentation(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Dimensional segmentation analysis."""
    d = await _svc.get_dashboard(tenant_id)
    return d["segmentation"]


@router.get("/nba-effectiveness", summary="Get NBA effectiveness analysis", description="Get accepted vs modified vs rejected next-best-action analysis.")
async def get_nba_effectiveness(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.READ)),
):
    """Accepted vs Modified vs Rejected NBA analysis."""
    d = await _svc.get_dashboard(tenant_id)
    return d["nba_effectiveness"]


@router.post("/accounts", summary="Upsert account funnel record", description="Create or update an account funnel record with cohort assignment and signal metadata.")
async def upsert_account(
    body: AccountUpsertRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.CREATE)),
):
    """Create or update account funnel record with cohort assignment."""
    return await _svc.upsert_account(
        tenant_id=tenant_id,
        company_name=body.company_name,
        seller_id=body.seller_id,
        intent_score=body.intent_score,
        intent_level=body.intent_level,
        sector=body.sector,
        company_size=body.company_size,
        signal_types=body.signal_types,
        signal_count=body.signal_count,
        critical_signal_count=body.critical_signal_count,
        source_diversity=body.source_diversity,
        nba_type=body.nba_type,
        nba_urgency=body.nba_urgency,
        original_nba_type=body.original_nba_type,
        seller_selected_action=body.seller_selected_action,
    )


@router.post("/events", summary="Record a funnel event", description="Record a funnel event: first_action, connection, meeting, opportunity, proposal, won, or lost.")
async def record_event(
    body: FunnelEventRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("signal_actions", PermissionAction.CREATE)),
):
    """Record a funnel event (first_action, connection, meeting, opportunity, proposal, won, lost)."""
    ok = await _svc.record_event(
        tenant_id=tenant_id,
        company_name=body.company_name,
        event_type=body.event_type,
        action_id=body.action_id,
        action_type=body.action_type,
        deal_value=body.deal_value,
        revenue=body.revenue,
    )
    return {"success": ok}
