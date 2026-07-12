from fastapi import APIRouter, Depends
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
    _: None = Depends(require_permission_dep("executive", PermissionAction.READ)),
):
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

    return dto
