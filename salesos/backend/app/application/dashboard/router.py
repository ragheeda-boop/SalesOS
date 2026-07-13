from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction
from app.application.dashboard.dto.dashboard_dto import DashboardDTO
from app.application.dashboard.aggregators.dashboard_aggregator import DashboardAggregator
from app.application.dashboard.queries.dashboard_query_handler import DashboardQueryHandler
from app.application.dashboard.queries.get_dashboard_query import DashboardQuery
from app.application.dashboard.services.decision_provider import DashboardDecisionProvider

router = APIRouter()


def _build_decision_provider():
    """Build DashboardDecisionProvider with Decision Platform wiring."""
    try:
        from domains.decision.context.in_memory_repo import InMemoryDecisionRepository
        from domains.decision.context.service import DecisionService
        from domains.decision.recommendation.engine import RecommendationEngine
        from app.application.dashboard.services.decision_platform_adapter import (
            DecisionServiceAdapter,
            RecommendationEngineAdapter,
        )

        repo = InMemoryDecisionRepository()
        decision_service = DecisionService(repository=repo)
        recommendation_engine = RecommendationEngine()
        return DashboardDecisionProvider(
            decision_service=DecisionServiceAdapter(decision_service),
            recommendation_engine=RecommendationEngineAdapter(recommendation_engine),
        )
    except Exception:
        return None


@router.get("/dashboard", response_model=DashboardDTO)
async def get_dashboard(
    query: DashboardQuery = Depends(),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    request: Request = None,
    _: None = Depends(require_permission_dep("executive", PermissionAction.READ)),
):
    cache = getattr(request.app.state, "cache", None) if request else None
    cache_key = f"dashboard:{tenant_id}:{query.period}:{','.join(sorted(query.fields)) if query.fields else 'all'}"

    if cache:
        cached = await cache.get(cache_key)
        if cached:
            from app.application.dashboard.dto.dashboard_dto import DashboardDTO
            return DashboardDTO(**cached)

    aggregator = DashboardAggregator(db, tenant_id)
    handler = DashboardQueryHandler(aggregator)
    dto = await handler.handle(query)

    dp = _build_decision_provider()
    if dp:
        try:
            widget_signals = {}
            if dto.missionCenter:
                widget_signals["missionCenter"] = dto.missionCenter
            if dto.decisionQueue:
                widget_signals["decisionQueue"] = dto.decisionQueue
            if dto.intelligenceFeed:
                widget_signals["intelligenceFeed"] = dto.intelligenceFeed
            if dto.recentActivity:
                widget_signals["recentActivity"] = dto.recentActivity

            if widget_signals:
                scored = await dp.score_dashboard(tenant_id, widget_signals)
                dto.scoredDecisions = scored.get("scored_decisions", [])
                dto.overallHealth = scored.get("overall_health", 1.0)
        except Exception:
            pass

    if cache:
        await cache.set(cache_key, dto.model_dump(mode="json"), ttl_seconds=60)

    return dto


# ── NBA Feed for Dashboard ─────────────────────────────────────────


class NBAFeedItem(BaseModel):
    id: str
    decision_id: str | None = None
    company_id: str
    company_name: str = ""
    action: str
    reason: str
    confidence: float
    confidence_label: str = "medium"
    priority: int = 0
    source: str = "rule"
    status: str = "pending"
    created_at: str = ""


class NBAFeedResponse(BaseModel):
    items: list[NBAFeedItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    generated_at: str
    cached: bool = False


@router.get("/dashboard/nba-feed", response_model=NBAFeedResponse)
async def get_nba_feed(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: str | None = Query(None, description="Filter by status: pending|accepted|rejected"),
    priority_min: int | None = Query(None, ge=0, le=100, description="Minimum priority threshold"),
    tenant_id: str = Depends(get_current_tenant_id),
    _: None = Depends(require_permission_dep("executive", PermissionAction.READ)),
):
    """NBA feed optimized for dashboard consumption.

    Returns cached, paginated, tenant-filtered Next Best Actions
    merged from the Decision Engine and NBA Engine.
    """
    from datetime import datetime, timezone as tz

    nba_items: list[NBAFeedItem] = []

    # ── Source 1: Decision Engine (runtime) ────────────────────
    decision_engine = getattr(request.app.state, "decision_engine", None)
    if decision_engine:
        try:
            raw_decisions = decision_engine.get_decisions(
                company_id="dashboard",
                tenant_id=tenant_id,
                limit=100,
            )
            for d in raw_decisions:
                if status_filter and d.get("status") != status_filter:
                    continue
                if priority_min is not None and d.get("priority", 0) < priority_min:
                    continue
                nba_items.append(NBAFeedItem(
                    id=d["decision_id"],
                    decision_id=d["decision_id"],
                    company_id=d.get("company_id", ""),
                    action=d.get("decision_type", ""),
                    reason=d.get("reasoning", ""),
                    confidence=d.get("confidence", 0.0),
                    confidence_label="high" if d.get("confidence", 0) >= 0.8 else "medium" if d.get("confidence", 0) >= 0.5 else "low",
                    priority=d.get("priority", 0),
                    source="decision_engine",
                    status=d.get("status", "suggested"),
                    created_at=d.get("created_at", ""),
                ))
        except Exception:
            pass

    # ── Source 2: NBA Engine (per-opportunity) ─────────────────
    nba_engine = getattr(request.app.state, "nba_engine", None)
    if nba_engine:
        try:
            from sqlalchemy import text as sa_text
            async with nba_engine._session_factory() as session:
                rows = await session.execute(
                    sa_text("""
                        SELECT DISTINCT ON (o.id)
                            o.id as opp_id, o.name, o.company_id,
                            c.name_ar as company_name,
                            o.stage, o.value, o.status as opp_status
                        FROM commercial_opportunities o
                        LEFT JOIN companies c ON c.id::text = o.company_id
                        WHERE o.tenant_id = :tid
                          AND o.status IN ('open', 'active')
                        ORDER BY o.id, o.value DESC
                        LIMIT 50
                    """),
                    {"tid": tenant_id},
                )
                opportunities = rows.mappings().all()

                for opp in opportunities:
                    opp_id = str(opp["opp_id"])
                    nba = await nba_engine.get_or_compute(opp_id, tenant_id)
                    if not nba:
                        continue

                    if status_filter and nba.status != status_filter:
                        continue
                    if priority_min is not None and int(nba.confidence * 100) < priority_min:
                        continue

                    nba_items.append(NBAFeedItem(
                        id=nba.id,
                        company_id=str(opp.get("company_id", "")),
                        company_name=str(opp.get("company_name") or ""),
                        action=nba.action,
                        reason=nba.reason,
                        confidence=max(0.0, min(1.0, nba.confidence)),
                        confidence_label=nba.confidence_label,
                        priority=int(nba.confidence * 100),
                        source=nba.source,
                        status=nba.status,
                        created_at=nba.created_at,
                    ))
        except Exception:
            pass

    # ── Sort and paginate ──────────────────────────────────────
    nba_items.sort(key=lambda x: (-x.priority, x.id))
    total = len(nba_items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = nba_items[start:end]

    return NBAFeedResponse(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
        generated_at=datetime.now(tz.utc).isoformat(),
        cached=False,
    )
