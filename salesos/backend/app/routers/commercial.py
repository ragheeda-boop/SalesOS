"""Commercial Platform API — all business domain endpoints."""

import logging
import os
from datetime import UTC, date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import safe_error_detail
from app.config import settings
from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

router = APIRouter()
logger = logging.getLogger(__name__)


class OpportunityUpdateBody(BaseModel):
    name: str | None = None
    value: float | None = None
    expected_close_date: date | None = None
    description: str | None = None


class OpportunityStageBody(BaseModel):
    stage: str
    reason: str | None = None


async def _analytics_input_from_db(db: AsyncSession, tenant_id: str):
    """Build AnalyticsInput from commercial_opportunities — never invent revenue."""
    from datetime import datetime, timedelta

    from sqlalchemy import func, select

    from domains.commercial.infrastructure.models import OpportunityModel
    from domains.revenue.analytics.service import AnalyticsInput

    now = datetime.now(UTC)
    period_start = now - timedelta(days=30)
    prev_start = now - timedelta(days=60)

    booked = (
        await db.execute(
            select(func.coalesce(func.sum(OpportunityModel.won_amount), 0.0)).where(
                OpportunityModel.tenant_id == tenant_id,
                OpportunityModel.status == "won",
                OpportunityModel.updated_at >= period_start,
            )
        )
    ).scalar() or 0.0

    previous_booked = (
        await db.execute(
            select(func.coalesce(func.sum(OpportunityModel.won_amount), 0.0)).where(
                OpportunityModel.tenant_id == tenant_id,
                OpportunityModel.status == "won",
                OpportunityModel.updated_at >= prev_start,
                OpportunityModel.updated_at < period_start,
            )
        )
    ).scalar() or 0.0

    # Fall back to opportunity value when won_amount is unset on won deals
    if booked == 0.0:
        booked = (
            await db.execute(
                select(func.coalesce(func.sum(OpportunityModel.value), 0.0)).where(
                    OpportunityModel.tenant_id == tenant_id,
                    OpportunityModel.status == "won",
                    OpportunityModel.updated_at >= period_start,
                )
            )
        ).scalar() or 0.0
    if previous_booked == 0.0:
        previous_booked = (
            await db.execute(
                select(func.coalesce(func.sum(OpportunityModel.value), 0.0)).where(
                    OpportunityModel.tenant_id == tenant_id,
                    OpportunityModel.status == "won",
                    OpportunityModel.updated_at >= prev_start,
                    OpportunityModel.updated_at < period_start,
                )
            )
        ).scalar() or 0.0

    expected = (
        await db.execute(
            select(func.coalesce(func.sum(OpportunityModel.value), 0.0)).where(
                OpportunityModel.tenant_id == tenant_id,
                OpportunityModel.status == "open",
            )
        )
    ).scalar() or 0.0

    open_count = (
        await db.execute(
            select(func.count())
            .select_from(OpportunityModel)
            .where(
                OpportunityModel.tenant_id == tenant_id,
                OpportunityModel.status == "open",
            )
        )
    ).scalar() or 0
    won_count = (
        await db.execute(
            select(func.count())
            .select_from(OpportunityModel)
            .where(
                OpportunityModel.tenant_id == tenant_id,
                OpportunityModel.status == "won",
            )
        )
    ).scalar() or 0
    lost_count = (
        await db.execute(
            select(func.count())
            .select_from(OpportunityModel)
            .where(
                OpportunityModel.tenant_id == tenant_id,
                OpportunityModel.status == "lost",
            )
        )
    ).scalar() or 0
    closed = won_count + lost_count
    conversion = (won_count / closed) if closed else 0.0
    coverage = (float(expected) / float(booked)) if booked else 0.0

    return AnalyticsInput(
        total_booked_revenue=float(booked),
        total_expected_revenue=float(expected),
        previous_booked_revenue=float(previous_booked),
        pipeline_coverage_ratio=float(coverage),
        stage_conversion_rate=float(conversion),
    ), open_count


# ── PostgreSQL-backed service factories ──


def _get_opp(db: AsyncSession):
    from domains.commercial.infrastructure.postgres_repositories import (
        PostgresOpportunityRepository,
    )
    from domains.commercial.opportunity.engine.service import OpportunityService

    return OpportunityService(PostgresOpportunityRepository(db))


def _get_pipe(db: AsyncSession):
    from domains.commercial.infrastructure.postgres_repositories import PostgresPipelineRepository
    from domains.commercial.pipeline.engine.service import PipelineService

    return PipelineService(PostgresPipelineRepository(db))


def _get_act(db: AsyncSession):
    from domains.commercial.activity.contracts.outcome_catalog import OutcomeCatalog
    from domains.commercial.activity.engine.service import ActivityService
    from domains.commercial.infrastructure.postgres_repositories import PostgresActivityRepository

    OutcomeCatalog.load_defaults()
    return ActivityService(PostgresActivityRepository(db))


def _get_quote(db: AsyncSession):
    from domains.commercial.infrastructure.postgres_repositories import PostgresQuoteRepository
    from domains.commercial.quote.engine.service import QuoteService

    return QuoteService(PostgresQuoteRepository(db))


def _get_proposal(db: AsyncSession):
    from domains.commercial.infrastructure.postgres_repositories import PostgresProposalRepository
    from domains.commercial.proposal.engine.service import ProposalService

    return ProposalService(PostgresProposalRepository(db))


def _get_contract(db: AsyncSession):
    from domains.commercial.contract.service import ContractService
    from domains.commercial.infrastructure.postgres_repositories import PostgresContractRepository

    return ContractService(PostgresContractRepository(db))


def _get_forecast(db: AsyncSession):
    from domains.commercial.infrastructure.postgres_repositories import PostgresForecastRepository
    from domains.revenue.forecast.service import ForecastService

    return ForecastService(PostgresForecastRepository(db))


def _get_analytics(db: AsyncSession):
    from domains.commercial.infrastructure.postgres_repositories import PostgresAnalyticsRepository
    from domains.revenue.analytics.registry import KPIRegistry
    from domains.revenue.analytics.service import AnalyticsService

    KPIRegistry.load_defaults()
    return AnalyticsService(PostgresAnalyticsRepository(db))


def _get_context(db: AsyncSession):
    from domains.commercial.infrastructure.postgres_repositories import PostgresDecisionRepository
    from domains.decision.context.service import DecisionService

    return DecisionService(PostgresDecisionRepository(db))


# ─────────────────────────────────────────────
# Opportunity Endpoints
# ─────────────────────────────────────────────


@router.post("/opportunities", status_code=201, tags=["Opportunities"])
async def create_opportunity(
    company_id: str = Query(...),
    name: str = Query(...),
    value: float = Query(0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.CREATE)),
):
    svc = _get_opp(db)
    opp = await svc.create_opportunity(tenant_id, company_id, name, value=value)
    return {"id": opp.id, "name": opp.name, "stage": opp.stage, "value": opp.value}


@router.get("/opportunities", tags=["Opportunities"])
async def list_opportunities(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.READ)),
    limit: int = Query(50, ge=1, le=500),
    cursor: str | None = Query(None),
):
    from domains.commercial.opportunity.contracts.repository import OpportunityQuery

    svc = _get_opp(db)
    offset = 0
    if cursor:
        try:
            offset = int(cursor)
        except (ValueError, TypeError):
            offset = 0
    result = await svc.query(
        OpportunityQuery(
            tenant_id=tenant_id, page_size=limit, page=offset // limit + 1 if limit else 1
        )
    )
    next_cursor = str(offset + limit) if offset + limit < result.total else None
    return {
        "items": [
            {
                "id": o.id,
                "name": o.name,
                "stage": o.stage,
                "value": o.value,
                "company_id": o.company_id,
            }
            for o in result.items
        ],
        "total": result.total,
        "next_cursor": next_cursor,
    }


@router.get("/opportunities/{opportunity_id}", tags=["Opportunities"])
async def get_opportunity(
    opportunity_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.READ)),
):
    svc = _get_opp(db)
    opp = await svc.get(opportunity_id)
    if not opp or getattr(opp, "tenant_id", None) != tenant_id:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {
        "id": opp.id,
        "name": opp.name,
        "stage": opp.stage,
        "value": opp.value,
        "company_id": opp.company_id,
        "status": opp.status.value if hasattr(opp.status, "value") else opp.status,
        "probability": getattr(opp, "probability", None),
        "owner_id": getattr(opp, "owner_id", ""),
        "description": getattr(opp, "description", ""),
    }


@router.put("/opportunities/{opportunity_id}", tags=["Opportunities"])
async def update_opportunity(
    opportunity_id: str,
    body: OpportunityUpdateBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    svc = _get_opp(db)
    try:
        opp = await svc.update_details(
            opportunity_id,
            tenant_id,
            name=body.name,
            value=body.value,
            expected_close_date=body.expected_close_date,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=safe_error_detail(exc, "Invalid update")) from exc
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {
        "id": opp.id,
        "name": opp.name,
        "stage": opp.stage,
        "value": opp.value,
        "company_id": opp.company_id,
        "status": opp.status.value if hasattr(opp.status, "value") else opp.status,
    }


@router.put("/opportunities/{opportunity_id}/stage", tags=["Opportunities"])
async def update_opportunity_stage_json(
    opportunity_id: str,
    body: OpportunityStageBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    """FE hooks + opportunity.store PUT JSON `{stage}` — commercial SoT table."""
    svc = _get_opp(db)
    existing = await svc.get(opportunity_id)
    if not existing or getattr(existing, "tenant_id", None) != tenant_id:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    try:
        opp = await svc.advance_stage(opportunity_id, body.stage)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid stage transition") from None
    return {
        "id": opp.id,
        "stage": opp.stage,
        "status": opp.status.value if hasattr(opp.status, "value") else opp.status,
    }


@router.post("/opportunities/{opportunity_id}/advance", tags=["Opportunities"])
async def advance_opportunity(
    opportunity_id: str,
    to_stage: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    svc = _get_opp(db)
    opp = await svc.advance_stage(opportunity_id, to_stage)
    return {"id": opp.id, "stage": opp.stage, "status": opp.status.value}


@router.post("/opportunities/{opportunity_id}/won", tags=["Opportunities"])
async def close_won(
    opportunity_id: str,
    amount: float = Query(None),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    svc = _get_opp(db)
    opp = await svc.close_won(opportunity_id, amount)
    return {"id": opp.id, "status": "won", "won_amount": opp.won_amount}


@router.post("/opportunities/{opportunity_id}/lost", tags=["Opportunities"])
async def close_lost(
    opportunity_id: str,
    reason: str = Query(""),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    svc = _get_opp(db)
    opp = await svc.close_lost(opportunity_id, reason)
    return {"id": opp.id, "status": "lost", "loss_reason": opp.loss_reason}


@router.post("/opportunities/{opportunity_id}/close-won", tags=["Opportunities"])
async def close_won_hyphen_alias(
    opportunity_id: str,
    won_amount: float | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    svc = _get_opp(db)
    existing = await svc.get(opportunity_id)
    if not existing or getattr(existing, "tenant_id", None) != tenant_id:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp = await svc.close_won(opportunity_id, won_amount)
    return {"id": opp.id, "status": "won", "won_amount": opp.won_amount}


@router.post("/opportunities/{opportunity_id}/close-lost", tags=["Opportunities"])
async def close_lost_hyphen_alias(
    opportunity_id: str,
    loss_reason: str = "",
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("opportunity", PermissionAction.UPDATE)),
):
    svc = _get_opp(db)
    existing = await svc.get(opportunity_id)
    if not existing or getattr(existing, "tenant_id", None) != tenant_id:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp = await svc.close_lost(opportunity_id, loss_reason)
    return {"id": opp.id, "status": "lost", "loss_reason": opp.loss_reason}


# ─────────────────────────────────────────────
# Pipeline Endpoints
# ─────────────────────────────────────────────


@router.post("/pipelines", status_code=201, tags=["Pipelines"])
async def create_pipeline(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.CREATE)),
):
    from domains.commercial.pipeline.contracts.models import PipelineDefinition

    svc = _get_pipe(db)
    pipe = PipelineDefinition.default_sales_pipeline(tenant_id, f"pipe-{tenant_id}")
    result = await svc.create_pipeline(pipe)
    return {"id": result.id, "name": result.name, "stages": [s.name for s in result.stages]}


@router.get("/pipelines", tags=["Pipelines"])
async def list_pipelines(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    svc = _get_pipe(db)
    pipes = await svc.list_pipelines(tenant_id)
    sliced = pipes[offset : offset + limit]
    return {
        "items": [{"id": p.id, "name": p.name, "stages": len(p.stages)} for p in sliced],
        "total": len(pipes),
        "limit": limit,
        "offset": offset,
    }


@router.get("/pipelines/{pipeline_id}/kpis", tags=["Pipelines"])
async def pipeline_kpis(
    pipeline_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("pipeline", PermissionAction.READ)),
):
    svc = _get_pipe(db)
    kpis = await svc.compute_kpis(pipeline_id, [])
    return {
        "pipeline_value": kpis.pipeline_value,
        "weighted": kpis.weighted_pipeline,
        "win_rate": kpis.win_rate,
    }


# ─────────────────────────────────────────────
# Activity Endpoints
# ─────────────────────────────────────────────


@router.post("/activity-sessions", status_code=201, tags=["Activities"])
async def create_session(
    target_id: str = Query(...),
    title: str = "Session",
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("activity", PermissionAction.CREATE)),
):
    svc = _get_act(db)
    session = await svc.create_session(tenant_id, title, target_id)
    return {"id": session.id, "title": session.title, "target_id": session.target_id}


@router.post("/activity-sessions/{session_id}/activities", tags=["Activities"])
async def add_activity(
    session_id: str,
    activity_type: str = Query(...),
    owner_id: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("activity", PermissionAction.CREATE)),
):
    from domains.commercial.activity.contracts.models import ActivityType

    svc = _get_act(db)
    atype = ActivityType(activity_type)
    act = await svc.add_activity(session_id, atype, owner_id)
    return {"id": act.id, "type": act.activity_type.value, "status": act.status.value}


@router.post("/activities/{activity_id}/complete", tags=["Activities"])
async def complete_activity(
    activity_id: str,
    session_id: str = Query(...),
    outcome_id: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("activity", PermissionAction.UPDATE)),
):
    svc = _get_act(db)
    result = await svc.complete_activity(session_id, activity_id, outcome_id)
    return {
        "activity_id": result.activity_id,
        "outcome": result.outcome_label,
        "business_action": result.business_action,
    }


# ─────────────────────────────────────────────
# Quote Endpoints
# ─────────────────────────────────────────────


@router.post("/quotes", status_code=201, tags=["Quotes"])
async def create_quote(
    opportunity_id: str = Query(...),
    title: str = "Quote",
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("quote", PermissionAction.CREATE)),
):
    svc = _get_quote(db)
    q = await svc.create_quote(tenant_id, opportunity_id=opportunity_id, title=title)
    return {"id": q.id, "title": q.title, "status": q.status.value, "version": q.version}


@router.post("/quotes/{quote_id}/lines", tags=["Quotes"])
async def add_quote_line(
    quote_id: str,
    description: str = Query(...),
    quantity: int = Query(1),
    unit_price: float = Query(0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("quote", PermissionAction.CREATE)),
):
    svc = _get_quote(db)
    line = await svc.add_line(quote_id, description, quantity=quantity, unit_price=unit_price)
    return {"id": line.id, "description": line.description, "line_total": line.line_total}


@router.post("/quotes/{quote_id}/submit", tags=["Quotes"])
async def submit_quote(
    quote_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("quote", PermissionAction.UPDATE)),
):
    svc = _get_quote(db)
    q = await svc.submit_for_approval(quote_id)
    return {"id": q.id, "status": q.status.value, "grand_total": q.grand_total}


@router.post("/quotes/{quote_id}/approve", tags=["Quotes"])
async def approve_quote(
    quote_id: str,
    approved_by: str = Query("manager"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("quote", PermissionAction.UPDATE)),
):
    svc = _get_quote(db)
    q = await svc.approve(quote_id, approved_by)
    return {"id": q.id, "status": q.status.value, "approved": q.approval.is_approved}


@router.post("/quotes/{quote_id}/send", tags=["Quotes"])
async def send_quote(
    quote_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("quote", PermissionAction.UPDATE)),
):
    svc = _get_quote(db)
    q = await svc.send(quote_id)
    return {"id": q.id, "status": q.status.value}


@router.post("/quotes/{quote_id}/accept", tags=["Quotes"])
async def accept_quote(
    quote_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("quote", PermissionAction.UPDATE)),
):
    svc = _get_quote(db)
    q = await svc.accept(quote_id)
    return {"id": q.id, "status": q.status.value, "grand_total": q.grand_total}


# ─────────────────────────────────────────────
# Proposal Endpoints
# ─────────────────────────────────────────────


@router.post("/proposals", status_code=201, tags=["Proposals"])
async def create_proposal(
    opportunity_id: str = Query(...),
    quote_id: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("proposal", PermissionAction.CREATE)),
):
    svc = _get_proposal(db)
    p = await svc.create_proposal(tenant_id, opportunity_id, quote_id)
    return {"id": p.id, "status": p.status.value, "sections": len(p.sections)}


@router.post("/proposals/{proposal_id}/deliver", tags=["Proposals"])
async def deliver_proposal(
    proposal_id: str,
    method: str = Query("email"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("proposal", PermissionAction.UPDATE)),
):
    svc = _get_proposal(db)
    p = await svc.approve(proposal_id, "auto")
    p = await svc.deliver(proposal_id, method=method)
    return {"id": p.id, "status": p.status.value, "delivery_method": p.delivery_method}


@router.post("/proposals/{proposal_id}/accept", tags=["Proposals"])
async def accept_proposal(
    proposal_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("proposal", PermissionAction.UPDATE)),
):
    svc = _get_proposal(db)
    p = await svc.approve(proposal_id, "auto")
    p = await svc.deliver(proposal_id)
    p = await svc.mark_viewed(proposal_id)
    p = await svc.accept(proposal_id)
    return {"id": p.id, "status": p.status.value}


# ─────────────────────────────────────────────
# Contract Endpoints
# ─────────────────────────────────────────────


@router.post("/contracts", status_code=201, tags=["Contracts"])
async def create_contract(
    opportunity_id: str = Query(...),
    quote_id: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("contract", PermissionAction.CREATE)),
):
    svc = _get_contract(db)
    c = await svc.create_contract(tenant_id, opportunity_id=opportunity_id, quote_id=quote_id)
    return {"id": c.id, "status": c.status.value}


@router.post("/contracts/{contract_id}/sign", tags=["Contracts"])
async def sign_contract(
    contract_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("contract", PermissionAction.UPDATE)),
):
    svc = _get_contract(db)
    c = await svc.sign(contract_id)
    c = await svc.activate(contract_id)
    return {"id": c.id, "status": c.status.value}


# ─────────────────────────────────────────────
# Forecast Endpoints
# ─────────────────────────────────────────────


@router.post("/forecast/run", tags=["Forecast"])
async def run_forecast(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("forecast", PermissionAction.CREATE)),
):
    from sqlalchemy import select

    from domains.commercial.infrastructure.models import OpportunityModel
    from domains.revenue.forecast.engine import CommercialInput

    svc = _get_forecast(db)

    is_demo = settings.demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
    if is_demo:
        logger.warning("Forecast running with DEMO MODE data for tenant=%s", tenant_id)
        inputs = [
            CommercialInput(
                opportunity_id="demo-1",
                opportunity_value=100000,
                opportunity_probability=0.5,
                historical_win_rate=0.7,
            )
        ]
    else:
        result = await db.execute(
            select(OpportunityModel)
            .where(
                OpportunityModel.tenant_id == tenant_id,
                OpportunityModel.status == "open",
            )
            .limit(200)
        )
        opportunities = result.scalars().all()
        if not opportunities:
            raise HTTPException(
                status_code=400,
                detail="No open opportunities for tenant; cannot run forecast without pipeline data",  # noqa: E501
            )
        inputs = [
            CommercialInput(
                opportunity_id=opp.id,
                opportunity_value=float(opp.value or 0),
                opportunity_probability=float(opp.probability or 0),
                opportunity_stage=opp.stage or "",
                historical_win_rate=0.0,
            )
            for opp in opportunities
        ]

    snap = await svc.create_forecast(tenant_id, inputs)
    return {
        "snapshot_id": snap.id,
        "total_expected": snap.total_expected_revenue,
        "total_weighted": snap.total_weighted_revenue,
        "confidence": snap.overall_confidence,
        "scenarios": list({line.scenario.value for line in snap.lines}),
        "input_count": len(inputs),
        "demo_mode": is_demo,
    }


@router.get("/forecast", tags=["Forecast"])
async def get_forecast(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("forecast", PermissionAction.READ)),
):
    svc = _get_forecast(db)
    latest = await svc.get_latest(tenant_id)
    if not latest:
        return {"message": "No forecast yet. POST /forecast/run to generate."}
    return {
        "snapshot_id": latest.id,
        "title": latest.title,
        "total_expected": latest.total_expected_revenue,
        "total_weighted": latest.total_weighted_revenue,
        "confidence": latest.overall_confidence,
        "risk": latest.overall_risk,
        "horizon_months": latest.horizon_months,
    }


# ─────────────────────────────────────────────
# Analytics Endpoints
# ─────────────────────────────────────────────


@router.post("/analytics/generate", tags=["Analytics"])
async def generate_analytics(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("analytics", PermissionAction.CREATE)),
):
    from datetime import datetime, timedelta

    svc = _get_analytics(db)
    now = datetime.now(UTC)

    is_demo = settings.demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
    if is_demo:
        logger.warning("Analytics generating with DEMO MODE data for tenant=%s", tenant_id)
        from domains.revenue.analytics.service import AnalyticsInput

        inputs = AnalyticsInput(
            total_booked_revenue=500000,
            total_expected_revenue=650000,
            previous_booked_revenue=400000,
        )
    else:
        inputs, _open_count = await _analytics_input_from_db(db, tenant_id)

    snap = await svc.generate_snapshot(tenant_id, inputs, now - timedelta(days=30), now)
    return {
        "snapshot_id": snap.id,
        "kpi_count": snap.total_kpis,
        "values": [
            {"kpi": v.kpi_id, "value": v.value, "change": v.change_percent} for v in snap.values
        ],
        "demo_mode": is_demo,
        "source": "demo" if is_demo else "commercial_opportunities",
    }


@router.get("/analytics/kpis", tags=["Analytics"])
async def analytics_kpis(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("analytics", PermissionAction.READ)),
):
    from domains.revenue.analytics.registry import KPIRegistry

    KPIRegistry.load_defaults()
    return {
        "kpis": [
            {"id": k.id, "name": k.name, "category": k.category.value, "formula": k.formula}
            for k in KPIRegistry.all().values()
        ]
    }


# ─────────────────────────────────────────────
# Decision Context + Recommendation Endpoints
# ─────────────────────────────────────────────


@router.post("/decision/context", tags=["Decisions"])
async def build_context(
    target_id: str = Query(...),
    target_type: str = Query("opportunity"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("decision", PermissionAction.CREATE)),
):
    from datetime import date, datetime

    from sqlalchemy import select

    from domains.commercial.infrastructure.models import OpportunityModel
    from domains.decision.context.models import DecisionFactor

    ctx = _get_context(db)
    factors: list[DecisionFactor] = []

    if target_type == "opportunity":
        row = (
            await db.execute(
                select(OpportunityModel).where(
                    OpportunityModel.id == target_id,
                    OpportunityModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if row:
            aging_days = 0
            if row.updated_at:
                aging_days = max(0, (datetime.now(UTC) - row.updated_at).days)
            factors.append(
                DecisionFactor(
                    source_layer="fact",
                    source_domain="pipeline",
                    key="stage_aging",
                    value=aging_days,
                    severity="critical"
                    if aging_days >= 14
                    else ("warning" if aging_days >= 7 else "info"),
                    label=f"{aging_days} days since last update in stage {row.stage}",
                )
            )
            factors.append(
                DecisionFactor(
                    source_layer="fact",
                    source_domain="pipeline",
                    key="opportunity_value",
                    value=float(row.value or 0),
                    severity="info",
                    label=f"Pipeline value {row.value} {row.currency}",
                )
            )
            if row.expected_close_date:
                days_to_close = (row.expected_close_date - date.today()).days
                factors.append(
                    DecisionFactor(
                        source_layer="fact",
                        source_domain="pipeline",
                        key="close_date_delta",
                        value=days_to_close,
                        severity="warning" if days_to_close < 0 else "info",
                        label=f"Days to expected close: {days_to_close}",
                    )
                )

    context = await ctx.build_context(tenant_id, target_id, target_type, factors=factors)
    return {
        "context_id": context.id,
        "target_id": context.target_id,
        "critical_factors": len(context.critical_factors),
        "warnings": len(context.warnings),
        "factor_count": len(factors),
        "source": "commercial_opportunities" if factors else "empty",
    }


@router.post("/recommendations/evaluate", tags=["Decisions"])
async def evaluate_recommendation(
    context_id: str = Query(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("decision", PermissionAction.READ)),
):
    ctx_svc = _get_context(db)
    context = await ctx_svc.get_context(context_id)
    if not context:
        return {"error": "Context not found"}

    from domains.decision.recommendation.engine import RecommendationEngine

    engine = RecommendationEngine()
    rec = await engine.evaluate(context)
    if not rec:
        return {"message": "No recommendation needed — deal is healthy."}
    return {
        "id": rec.id,
        "title": rec.title,
        "description": rec.description,
        "reasoning": rec.reasoning,
        "confidence": rec.confidence,
        "risk": rec.risk,
        "expected_impact": rec.expected_impact,
        "alternatives": [
            {"title": a.title, "description": a.description} for a in rec.alternatives
        ],
        "evidence": [{"factor": e.key, "narrative": e.narrative} for e in rec.evidence],
    }


# ─────────────────────────────────────────────
# Workspace (Aggregated Dashboard)
# ─────────────────────────────────────────────


@router.get("/workspace", tags=["Workspace"])
async def workspace(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("workspace", PermissionAction.READ)),
):
    """Rich aggregated workspace — powers the main dashboard UI."""
    from datetime import datetime

    result: dict[str, Any] = {
        "tenant_id": tenant_id,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    # Forecast
    try:
        fsvc = _get_forecast(db)
        latest = await fsvc.get_latest(tenant_id)
        if latest:
            result["forecast"] = {
                "total_expected": latest.total_expected_revenue,
                "total_weighted": latest.total_weighted_revenue,
                "confidence": round(latest.overall_confidence, 2),
                "risk": round(latest.overall_risk, 2),
                "horizon_months": latest.horizon_months,
                "status": "on_track" if latest.overall_confidence > 0.7 else "needs_review",
            }
        else:
            result["forecast"] = {"message": "Generate forecast via POST /api/v1/forecast/run"}
    except Exception as e:
        result["forecast"] = {"error": safe_error_detail(e, "Failed to load forecast")}

    # Opportunities summary
    try:
        from domains.commercial.opportunity.contracts.repository import OpportunityQuery

        opp_result = await _get_opp(db).query(OpportunityQuery(tenant_id=tenant_id, page_size=100))
        total_value = sum(o.value for o in opp_result.items)
        won = sum(1 for o in opp_result.items if o.status.value == "won")
        lost = sum(1 for o in opp_result.items if o.status.value == "lost")
        open_opps = [o for o in opp_result.items if o.status.value == "open"]
        result["opportunities"] = {
            "total": opp_result.total,
            "total_value": total_value,
            "won": won,
            "lost": lost,
            "win_rate": round(won / (won + lost), 2) if (won + lost) > 0 else 0,
            "recent": [
                {
                    "id": o.id,
                    "name": o.name,
                    "stage": o.stage,
                    "value": o.value,
                    "company_id": o.company_id,
                }
                for o in open_opps[:5]
            ],
        }
    except Exception as e:
        result["opportunities"] = {"error": safe_error_detail(e, "Failed to load opportunities")}

    # Pipeline summary
    try:
        pipes = await _get_pipe(db).list_pipelines(tenant_id)
        result["pipelines"] = [{"id": p.id, "name": p.name, "stages": len(p.stages)} for p in pipes]
    except Exception:
        result["pipelines"] = []

    # Analytics KPIs from real commercial_opportunities (or demo when DEMO_MODE)
    try:
        from datetime import timedelta

        asvc = _get_analytics(db)
        is_demo = settings.demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
        if is_demo:
            from domains.revenue.analytics.service import AnalyticsInput

            inputs = AnalyticsInput(
                total_booked_revenue=500000,
                total_expected_revenue=650000,
                previous_booked_revenue=400000,
                forecast_accuracy=0.82,
            )
            open_count = 0
        else:
            inputs, open_count = await _analytics_input_from_db(db, tenant_id)
        await asvc.generate_snapshot(
            tenant_id,
            inputs,
            datetime.now(UTC) - timedelta(days=30),
            datetime.now(UTC),
        )
        latest_a = await asvc.get_latest(tenant_id)
        if latest_a:
            result["kpis"] = {}
            for v in latest_a.values:
                result["kpis"][v.kpi_id] = {"value": v.value, "change": v.change_percent}
        result["analytics_meta"] = {
            "demo_mode": is_demo,
            "open_opportunities": open_count,
            "source": "demo" if is_demo else "commercial_opportunities",
        }
    except Exception:
        result["kpis"] = {}

    # Recommendations for open opportunities — factors from live opportunity rows
    try:
        import asyncio as _asyncio

        from domains.decision.context.models import DecisionFactor

        ctx_svc = _get_context(db)
        open_opps = [
            o
            for o in (opp_result.items if "opp_result" in dir() else [])
            if o.status.value == "open"
        ]
        recs = []
        if open_opps:
            shared = [
                DecisionFactor(
                    source_layer="fact",
                    source_domain="pipeline",
                    key="open_pipeline_count",
                    value=len(open_opps),
                    severity="info",
                    label=f"{len(open_opps)} open opportunities",
                )
            ]
            contexts = await ctx_svc.build_contexts(
                tenant_id, [o.id for o in open_opps], factors=shared
            )
            from domains.decision.recommendation.engine import RecommendationEngine

            eng = RecommendationEngine()
            results = await _asyncio.gather(
                *[eng.evaluate(ctx) if ctx else _asyncio.sleep(0, result=None) for ctx in contexts]
            )
            for opp, rec in zip(open_opps, results, strict=False):
                if rec:
                    recs.append(
                        {
                            "id": rec.id,
                            "title": rec.title,
                            "confidence": rec.confidence,
                            "reasoning": rec.reasoning,
                            "target_id": opp.id,
                        }
                    )
        result["recommendations"] = recs
        result["recommendations_count"] = len(recs)
    except Exception:
        result["recommendations"] = []

    # Today overview — computed from workspace aggregates, never hardcoded demo SAR
    today_str = datetime.now(UTC).strftime("%A, %Y-%m-%d")
    opp_block = result.get("opportunities") or {}
    forecast_block = result.get("forecast") or {}
    total_value = float(opp_block.get("total_value") or 0) if isinstance(opp_block, dict) else 0.0
    conf = forecast_block.get("confidence") if isinstance(forecast_block, dict) else None
    open_n = int(opp_block.get("total") or 0) if isinstance(opp_block, dict) else 0
    if conf is None:
        pipeline_health = "unknown"
    elif float(conf) >= 0.7:
        pipeline_health = "healthy"
    elif float(conf) >= 0.4:
        pipeline_health = "needs_review"
    else:
        pipeline_health = "at_risk"
    if open_n == 0 and total_value == 0:
        pipeline_health = "empty"

    result["today"] = {
        "date": today_str,
        "revenue_pipeline_sar": round(total_value, 2),
        "forecast_confidence": conf,
        "pipeline_health": pipeline_health,
        "open_opportunities": open_n,
        "companies_at_risk": result.get("recommendations_count", 0),
        "source": "workspace_aggregates",
    }

    return result
