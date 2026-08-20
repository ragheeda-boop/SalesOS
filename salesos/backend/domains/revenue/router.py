"""Revenue Planning Router — Forecast, Quota, Territory endpoints.

P1-6: Forecast now uses Postgres-backed repository (per-request via DI).
Quota and Territory remain in-memory until Postgres repos + migrations are added.
Router is now mounted in boot/routers.py under /api/v1/revenue-planning.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, get_current_tenant_id, require_permission_dep
from sdk.permissions import PermissionAction

from domains.revenue.forecast.engine import CommercialInput, ForecastEngine
from domains.revenue.forecast.in_memory_repo import InMemoryForecastRepository
from domains.revenue.forecast.service import ForecastService
from domains.revenue.forecast.models import TimeSeriesDataPoint

from domains.revenue.quota.models import QuotaPeriod
from domains.revenue.quota.in_memory_repo import InMemoryQuotaRepository
from domains.revenue.quota.service import QuotaService

from domains.revenue.territory.in_memory_repo import InMemoryTerritoryRepository
from domains.revenue.territory.service import TerritoryService

from pydantic import BaseModel, Field


router = APIRouter()

# ── Per-request service factories (P1-6) ──
# Forecast: Postgres-backed. Quota/Territory: in-memory (pending Postgres repos).


def _forecast_svc(db: AsyncSession = Depends(get_db_session)) -> ForecastService:
    try:
        from domains.commercial.infrastructure.postgres_repositories import (
            PostgresForecastRepository,
        )
        return ForecastService(PostgresForecastRepository(db))
    except ImportError:
        return ForecastService(InMemoryForecastRepository())


def _quota_svc(db: AsyncSession = Depends(get_db_session)) -> QuotaService:
    """P1-6: Quota now uses Postgres-backed repo."""
    try:
        from domains.commercial.infrastructure.postgres_repositories import (
            PostgresQuotaRepository,
        )
        return QuotaService(PostgresQuotaRepository(db))
    except ImportError:
        return QuotaService(InMemoryQuotaRepository())


def _territory_svc(db: AsyncSession = Depends(get_db_session)) -> TerritoryService:
    """P1-6: Territory now uses Postgres-backed repo."""
    try:
        from domains.commercial.infrastructure.postgres_repositories import (
            PostgresTerritoryRepository,
        )
        return TerritoryService(PostgresTerritoryRepository(db))
    except ImportError:
        return TerritoryService(InMemoryTerritoryRepository())


_forecast_engine = ForecastEngine()


# ── Request / Response Schemas ──

class CommercialInputSchema(BaseModel):
    opportunity_id: str = ""
    opportunity_value: float = 0.0
    opportunity_probability: float = 0.0
    opportunity_stage: str = ""
    has_recent_activity: bool = False
    days_in_stage: float = 0.0
    sla_days: int = 30
    quote_approved: bool = False
    quote_value: float = 0.0
    contract_signed: bool = False
    contract_value: float = 0.0
    historical_win_rate: float = 0.0
    rep_id: str = ""
    rep_name: str = ""
    region: str = ""
    product: str = ""


class CreateForecastRequest(BaseModel):
    inputs: list[CommercialInputSchema]
    horizon_months: int = 3
    title: str = ""


class TimeSeriesPointSchema(BaseModel):
    date: datetime
    value: float
    rep_id: str = ""
    region: str = ""
    product: str = ""


class CombinedForecastRequest(BaseModel):
    inputs: list[CommercialInputSchema]
    historical: list[TimeSeriesPointSchema]
    horizon_months: int = 3
    ts_weight: float = 0.4
    pipeline_weight: float = 0.6


class CreateQuotaRequest(BaseModel):
    rep_id: str
    target_amount: float
    period: str = "quarterly"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    rep_name: str = ""


class UpdateAttainmentRequest(BaseModel):
    attained_amount: float


class ForecastAttainmentRequest(BaseModel):
    rep_id: str
    closed_revenue: float
    period_days_elapsed: float
    total_period_days: float = 90.0


class CreateTerritoryRequest(BaseModel):
    name: str
    region: str = ""
    rep_id: str = ""
    rep_name: str = ""
    account_ids: list[str] = Field(default_factory=list)


class UpdateTerritoryRequest(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    rep_id: Optional[str] = None
    rep_name: Optional[str] = None


class AssignAccountsRequest(BaseModel):
    account_ids: list[str]


class MoveAccountRequest(BaseModel):
    from_territory_id: str
    to_territory_id: str
    account_id: str


class CoverageAnalysisRequest(BaseModel):
    account_values: dict[str, float] = Field(default_factory=dict)


class LoadBalanceRequest(BaseModel):
    max_accounts_per_rep: Optional[int] = None
    account_values: dict[str, float] = Field(default_factory=dict)


# ── Forecast Endpoints ──

@router.post("/forecast", dependencies=[Depends(require_permission_dep("forecast", PermissionAction.CREATE))])
async def create_forecast(
    body: CreateForecastRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    forecast_svc: ForecastService = Depends(_forecast_svc),
):
    inputs = [CommercialInput(**i.model_dump()) for i in body.inputs]
    snap = await forecast_svc.create_forecast(tenant_id, inputs, body.horizon_months, body.title)
    return {
        "id": snap.id,
        "title": snap.title,
        "total_expected_revenue": snap.total_expected_revenue,
        "total_weighted_revenue": snap.total_weighted_revenue,
        "overall_confidence": snap.overall_confidence,
        "overall_risk": snap.overall_risk,
        "line_count": len(snap.lines),
    }


@router.get("/forecast", dependencies=[Depends(require_permission_dep("forecast", PermissionAction.READ))])
async def list_forecasts(
    tenant_id: str = Depends(get_current_tenant_id),
    forecast_svc: ForecastService = Depends(_forecast_svc),
    limit: int = Query(10, ge=1, le=100),
):
    snapshots = await forecast_svc.list_snapshots(tenant_id, limit)
    return [
        {
            "id": s.id,
            "title": s.title,
            "total_expected_revenue": s.total_expected_revenue,
            "status": s.status.value,
            "created_at": s.created_at.isoformat(),
        }
        for s in snapshots
    ]


@router.get("/forecast/{snapshot_id}", dependencies=[Depends(require_permission_dep("forecast", PermissionAction.READ))])
async def get_forecast(snapshot_id: str, forecast_svc: ForecastService = Depends(_forecast_svc)):
    snap = await forecast_svc.get(snapshot_id)
    if not snap:
        raise HTTPException(404, "Forecast not found")
    return {
        "id": snap.id,
        "title": snap.title,
        "total_expected_revenue": snap.total_expected_revenue,
        "total_weighted_revenue": snap.total_weighted_revenue,
        "overall_confidence": snap.overall_confidence,
        "status": snap.status.value,
        "lines_count": len(snap.lines),
    }


@router.post("/forecast/{snapshot_id}/finalize", dependencies=[Depends(require_permission_dep("forecast", PermissionAction.UPDATE))])
async def finalize_forecast(snapshot_id: str, forecast_svc: ForecastService = Depends(_forecast_svc)):
    snap = await forecast_svc.finalize(snapshot_id)
    return {"id": snap.id, "status": snap.status.value}


@router.get("/forecast/{snapshot_id}/explain", dependencies=[Depends(require_permission_dep("forecast", PermissionAction.READ))])
async def explain_forecast(snapshot_id: str, forecast_svc: ForecastService = Depends(_forecast_svc)):
    snap = await forecast_svc.get(snapshot_id)
    if not snap:
        raise HTTPException(404, "Forecast not found")
    return forecast_svc.explain(snap)


@router.get("/forecast/{snapshot_id}/breakdown/{dimension}", dependencies=[Depends(require_permission_dep("forecast", PermissionAction.READ))])
async def breakdown_forecast(snapshot_id: str, dimension: str, forecast_svc: ForecastService = Depends(_forecast_svc)):
    snap = await forecast_svc.get(snapshot_id)
    if not snap:
        raise HTTPException(404, "Forecast not found")
    engine = ForecastEngine()
    result = engine.breakdown(snap, dimension)
    return [
        {"dimension": b.dimension, "value": b.value,
         "expected_revenue": b.expected_revenue, "weighted_revenue": b.weighted_revenue,
         "confidence": b.confidence, "line_count": b.line_count}
        for b in result
    ]


@router.post("/forecast/combined", dependencies=[Depends(require_permission_dep("forecast", PermissionAction.CREATE))])
async def create_combined_forecast(
    body: CombinedForecastRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    forecast_svc: ForecastService = Depends(_forecast_svc),
):
    inputs = [CommercialInput(**i.model_dump()) for i in body.inputs]
    historical = [TimeSeriesDataPoint(**h.model_dump()) for h in body.historical]
    result = _forecast_engine.combined_forecast(
        inputs, historical, body.horizon_months,
        body.ts_weight, body.pipeline_weight,
    )
    return {
        "combined_value": result.combined_value,
        "time_series_value": result.time_series_value,
        "pipeline_value": result.pipeline_value,
        "confidence_lower": result.confidence_lower,
        "confidence_upper": result.confidence_upper,
        "method_confidence": result.method_confidence,
    }


# ── Quota Endpoints ──

@router.post("/quotas", dependencies=[Depends(require_permission_dep("quota", PermissionAction.CREATE))])
async def create_quota(
    body: CreateQuotaRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    quota_svc: QuotaService = Depends(_quota_svc),
):
    try:
        period = QuotaPeriod(body.period)
    except ValueError:
        raise HTTPException(400, f"Invalid period: {body.period}. Use: monthly, quarterly, yearly")
    q = await quota_svc.create_quota(
        tenant_id, body.rep_id, body.target_amount,
        period=period, start_date=body.start_date, end_date=body.end_date,
        rep_name=body.rep_name,
    )
    return {
        "id": q.id, "rep_id": q.rep_id, "target_amount": q.target_amount,
        "period": q.period.value, "status": q.status.value,
    }


@router.get("/quotas", dependencies=[Depends(require_permission_dep("quota", PermissionAction.READ))])
async def list_quotas(
    tenant_id: str = Depends(get_current_tenant_id),
    quota_svc: QuotaService = Depends(_quota_svc),
    rep_id: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    quotas = await quota_svc.list_quotas(tenant_id, rep_id, period, status)
    return [
        {"id": q.id, "rep_id": q.rep_id, "rep_name": q.rep_name,
         "target_amount": q.target_amount, "attained_amount": q.attained_amount,
         "attainment_percent": q.attainment_percent, "period": q.period.value,
         "status": q.status.value}
        for q in quotas
    ]


@router.get("/quotas/{quota_id}", dependencies=[Depends(require_permission_dep("quota", PermissionAction.READ))])
async def get_quota(quota_id: str, quota_svc: QuotaService = Depends(_quota_svc)):
    q = await quota_svc.get_quota(quota_id)
    if not q:
        raise HTTPException(404, "Quota not found")
    return {
        "id": q.id, "rep_id": q.rep_id, "rep_name": q.rep_name,
        "target_amount": q.target_amount, "attained_amount": q.attained_amount,
        "attainment_percent": q.attainment_percent, "remaining_amount": q.remaining_amount,
        "period": q.period.value, "status": q.status.value,
        "is_on_track": q.is_on_track,
    }


@router.put("/quotas/{quota_id}/attainment", dependencies=[Depends(require_permission_dep("quota", PermissionAction.UPDATE))])
async def update_attainment(quota_id: str, body: UpdateAttainmentRequest, quota_svc: QuotaService = Depends(_quota_svc)):
    q = await quota_svc.update_attainment(quota_id, body.attained_amount)
    return {
        "id": q.id, "attained_amount": q.attained_amount,
        "attainment_percent": q.attainment_percent, "status": q.status.value,
    }


@router.post("/quotas/forecast-attainment", dependencies=[Depends(require_permission_dep("quota", PermissionAction.READ))])
async def forecast_attainment(
    body: ForecastAttainmentRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    quota_svc: QuotaService = Depends(_quota_svc),
):
    result = await quota_svc.forecast_attainment(
        tenant_id, body.rep_id, body.closed_revenue,
        body.period_days_elapsed, body.total_period_days,
    )
    return {
        "quota_id": result.quota_id, "rep_id": result.rep_id,
        "current_velocity": result.current_velocity,
        "days_remaining": result.days_remaining,
        "projected_attainment": result.projected_attainment,
        "projected_attainment_percent": result.projected_attainment_percent,
        "will_hit_target": result.will_hit_target,
        "confidence": result.confidence,
    }


@router.get("/quotas/team/aggregate", dependencies=[Depends(require_permission_dep("quota", PermissionAction.READ))])
async def team_aggregate(
    tenant_id: str = Depends(get_current_tenant_id),
    quota_svc: QuotaService = Depends(_quota_svc),
):
    team = await quota_svc.get_team_aggregate(tenant_id)
    return {
        "total_targets": team.total_targets,
        "total_attained": team.total_attained,
        "overall_attainment_percent": team.overall_attainment_percent,
        "rep_count": team.rep_count,
        "reps_on_track": team.reps_on_track,
        "reps_at_risk": team.reps_at_risk,
        "reps_missed": team.reps_missed,
    }


@router.post("/quotas/snapshot", dependencies=[Depends(require_permission_dep("quota", PermissionAction.CREATE))])
async def take_quota_snapshot(
    tenant_id: str = Depends(get_current_tenant_id),
    quota_svc: QuotaService = Depends(_quota_svc),
    period_label: str = Query(""),
):
    snap = await quota_svc.take_snapshot(tenant_id, period_label)
    return {
        "id": snap.id, "period_label": snap.period_label,
        "total_target": snap.total_target, "total_attained": snap.total_attained,
        "overall_attainment": snap.overall_attainment,
    }


# ── Territory Endpoints ──

@router.post("/territories", dependencies=[Depends(require_permission_dep("territory", PermissionAction.CREATE))])
async def create_territory(
    body: CreateTerritoryRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    territory_svc: TerritoryService = Depends(_territory_svc),
):
    t = await territory_svc.create_territory(
        tenant_id, body.name, body.region, body.rep_id, body.rep_name, body.account_ids,
    )
    return {
        "id": t.id, "name": t.name, "region": t.region,
        "rep_id": t.rep_id, "account_count": t.account_count,
    }


@router.get("/territories", dependencies=[Depends(require_permission_dep("territory", PermissionAction.READ))])
async def list_territories(
    tenant_id: str = Depends(get_current_tenant_id),
    territory_svc: TerritoryService = Depends(_territory_svc),
    rep_id: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
):
    items = await territory_svc.list_territories(tenant_id, rep_id, region)
    return [
        {"id": t.id, "name": t.name, "region": t.region,
         "rep_id": t.rep_id, "rep_name": t.rep_name,
         "account_count": t.account_count}
        for t in items
    ]


@router.get("/territories/{territory_id}", dependencies=[Depends(require_permission_dep("territory", PermissionAction.READ))])
async def get_territory(territory_id: str, territory_svc: TerritoryService = Depends(_territory_svc)):
    t = await territory_svc.get_territory(territory_id)
    if not t:
        raise HTTPException(404, "Territory not found")
    return {
        "id": t.id, "name": t.name, "region": t.region,
        "rep_id": t.rep_id, "rep_name": t.rep_name,
        "account_ids": t.account_ids, "account_count": t.account_count,
    }


@router.put("/territories/{territory_id}", dependencies=[Depends(require_permission_dep("territory", PermissionAction.UPDATE))])
async def update_territory(territory_id: str, body: UpdateTerritoryRequest, territory_svc: TerritoryService = Depends(_territory_svc)):
    t = await territory_svc.update_territory(
        territory_id, body.name, body.region, body.rep_id, body.rep_name,
    )
    return {"id": t.id, "name": t.name, "region": t.region, "rep_id": t.rep_id}


@router.delete("/territories/{territory_id}", dependencies=[Depends(require_permission_dep("territory", PermissionAction.DELETE))])
async def delete_territory(territory_id: str, territory_svc: TerritoryService = Depends(_territory_svc)):
    result = await territory_svc.delete_territory(territory_id)
    if not result:
        raise HTTPException(404, "Territory not found")
    return {"deleted": True}


@router.post("/territories/{territory_id}/assign", dependencies=[Depends(require_permission_dep("territory", PermissionAction.UPDATE))])
async def assign_accounts(territory_id: str, body: AssignAccountsRequest, territory_svc: TerritoryService = Depends(_territory_svc)):
    t = await territory_svc.assign_accounts(territory_id, body.account_ids)
    return {"id": t.id, "account_count": t.account_count, "account_ids": t.account_ids}


@router.post("/territories/{territory_id}/unassign", dependencies=[Depends(require_permission_dep("territory", PermissionAction.UPDATE))])
async def unassign_accounts(territory_id: str, body: AssignAccountsRequest, territory_svc: TerritoryService = Depends(_territory_svc)):
    t = await territory_svc.unassign_accounts(territory_id, body.account_ids)
    return {"id": t.id, "account_count": t.account_count}


@router.post("/territories/move-account", dependencies=[Depends(require_permission_dep("territory", PermissionAction.UPDATE))])
async def move_account(body: MoveAccountRequest, territory_svc: TerritoryService = Depends(_territory_svc)):
    from_t, to_t = await territory_svc.move_account(
        body.from_territory_id, body.to_territory_id, body.account_id,
    )
    return {
        "from_territory": {"id": from_t.id, "account_count": from_t.account_count},
        "to_territory": {"id": to_t.id, "account_count": to_t.account_count},
    }


@router.post("/territories/coverage-analysis", dependencies=[Depends(require_permission_dep("territory", PermissionAction.READ))])
async def coverage_analysis(
    tenant_id: str = Depends(get_current_tenant_id),
    territory_svc: TerritoryService = Depends(_territory_svc),
    body: CoverageAnalysisRequest = CoverageAnalysisRequest(),
):
    summary = await territory_svc.coverage_analysis(tenant_id, body.account_values)
    return {
        "total_territories": summary.total_territories,
        "total_accounts": summary.total_accounts,
        "total_reps": summary.total_reps,
        "avg_accounts_per_rep": summary.avg_accounts_per_rep,
        "per_rep": [
            {"rep_id": p.rep_id, "rep_name": p.rep_name,
             "territory_count": p.territory_count, "total_accounts": p.total_accounts,
             "total_pipeline_value": p.total_pipeline_value}
            for p in summary.per_rep
        ],
    }


@router.post("/territories/find-gaps", dependencies=[Depends(require_permission_dep("territory", PermissionAction.READ))])
async def find_gaps(
    tenant_id: str = Depends(get_current_tenant_id),
    territory_svc: TerritoryService = Depends(_territory_svc),
    known_account_ids: list[str] = Query(..., description="All known account IDs"),
):
    gaps = await territory_svc.find_gaps(tenant_id, known_account_ids)
    return [
        {"account_id": g.account_id, "account_name": g.account_name, "pipeline_value": g.pipeline_value}
        for g in gaps
    ]


@router.post("/territories/load-balance", dependencies=[Depends(require_permission_dep("territory", PermissionAction.READ))])
async def load_balance(
    tenant_id: str = Depends(get_current_tenant_id),
    territory_svc: TerritoryService = Depends(_territory_svc),
    body: LoadBalanceRequest = LoadBalanceRequest(),
):
    recs = await territory_svc.load_balance(tenant_id, body.max_accounts_per_rep, body.account_values)
    return [
        {"account_id": r.account_id, "from_rep_id": r.from_rep_id,
         "to_rep_id": r.to_rep_id, "reason": r.reason, "impact_score": r.impact_score}
        for r in recs
    ]
