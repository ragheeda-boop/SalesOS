from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import require_role_dep

router = APIRouter(
    tags=["Admin - Decision Adoption"],
    dependencies=[Depends(require_role_dep("admin"))],
)


class DecisionWidgetStatus(BaseModel):
    widget_id: str
    widget_name: str
    decision_context_type: str
    uses_decision_provider: bool
    uses_nba_feed: bool
    last_scored_at: str | None = None
    last_health_score: float | None = None
    consecutive_failures: int
    status: str


class DecisionAdoptionResponse(BaseModel):
    total_widgets: int
    using_decision_provider: int
    using_nba_feed: int
    adoption_percentage: float
    health: dict[str, int]
    registered_at: str
    widgets: list[DecisionWidgetStatus]


@router.get("/decision-adoption", response_model=DecisionAdoptionResponse)
async def get_decision_adoption():
    """Admin endpoint: DecisionProvider adoption metrics across all dashboard widgets."""
    from runtime.decision_runtime.registry import DecisionWidgetRegistry

    registry = DecisionWidgetRegistry.get_instance()
    metrics = registry.get_adoption_metrics()

    return DecisionAdoptionResponse(
        total_widgets=metrics["total_widgets"],
        using_decision_provider=metrics["using_decision_provider"],
        using_nba_feed=metrics["using_nba_feed"],
        adoption_percentage=metrics["adoption_percentage"],
        health=metrics["health"],
        registered_at=metrics["registered_at"],
        widgets=[
            DecisionWidgetStatus(
                widget_id=w["widget_id"],
                widget_name=w["widget_name"],
                decision_context_type=w["decision_context_type"],
                uses_decision_provider=w["uses_decision_provider"],
                uses_nba_feed=w["uses_nba_feed"],
                last_scored_at=w.get("last_scored_at"),
                last_health_score=w.get("last_health_score"),
                consecutive_failures=w["consecutive_failures"],
                status=w["status"],
            )
            for w in metrics["widgets"]
        ],
    )


@router.post("/decision-adoption/health-check")
async def run_decision_health_check():
    """Admin endpoint: Run health checks on all decision-enabled widgets."""
    from runtime.decision_runtime.registry import DecisionWidgetRegistry

    registry = DecisionWidgetRegistry.get_instance()
    results = registry.run_health_checks()
    return {"results": {k: v.value for k, v in results.items()}, "total": len(results)}
