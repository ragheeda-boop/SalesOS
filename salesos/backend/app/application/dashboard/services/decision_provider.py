"""DashboardDecisionProvider — scores dashboard widget signals via Decision Platform.

Collects widget signals (from mission-center, decision-queue, intelligence-feed, etc.),
converts them to DecisionContext factors, and returns scored recommendations.

Flow: Widget Signals → DecisionContext → RecommendationEngine → Scored Decisions
"""

from __future__ import annotations

import logging
from typing import Any

from sdk.scoring.interfaces import (
    DecisionContext,
    DecisionFactor,
    DecisionServiceProtocol,
    Recommendation,
    RecommendationEngineProtocol,
)

logger = logging.getLogger(__name__)


class DashboardDecisionProvider:
    """Scores dashboard widget data through the Decision Platform.

    Wraps DecisionService + RecommendationEngine to produce scored decisions
    for the dashboard's widget signals. Non-blocking: failures degrade gracefully.
    """

    def __init__(
        self,
        decision_service: DecisionServiceProtocol,
        recommendation_engine: RecommendationEngineProtocol,
    ):
        self._decision_service = decision_service
        self._recommendation_engine = recommendation_engine

    async def score_dashboard(
        self,
        tenant_id: str,
        widget_signals: dict[str, Any],
    ) -> dict[str, Any]:
        """Score all dashboard widget signals and return scored decisions.

        Args:
            tenant_id: Current tenant.
            widget_signals: Raw widget data keyed by widget ID.
                Expected keys: decisionQueue, intelligenceFeed, missionCenter, etc.

        Returns:
            dict with "scored_decisions" list and "overall_health" float.
        """
        factors = self._collect_factors(widget_signals)
        if not factors:
            return {"scored_decisions": [], "overall_health": 1.0}

        try:
            context = await self._decision_service.build_context(
                tenant_id=tenant_id,
                target_id="dashboard",
                target_type="dashboard",
                factors=factors,
            )
            recommendation = await self._recommendation_engine.evaluate(context)
        except Exception as exc:
            logger.warning("DashboardDecisionProvider scoring failed (non-blocking): %s", exc)
            return {"scored_decisions": [], "overall_health": 0.0}

        scored = self._build_scored_decisions(factors, recommendation)
        overall_health = self._compute_overall_health(factors)

        return {
            "scored_decisions": scored,
            "overall_health": overall_health,
        }

    def _collect_factors(self, widget_signals: dict[str, Any]) -> list[DecisionFactor]:
        """Convert widget signal data into DecisionContext factors."""
        factors: list[DecisionFactor] = []

        for widget_id, widget_data in widget_signals.items():
            if widget_data is None:
                continue

            if widget_id == "decisionQueue":
                factors.extend(self._factors_from_decision_queue(widget_data))
            elif widget_id == "intelligenceFeed":
                factors.extend(self._factors_from_intelligence_feed(widget_data))
            elif widget_id == "missionCenter":
                factors.extend(self._factors_from_mission_center(widget_data))
            elif widget_id == "recentActivity":
                factors.extend(self._factors_from_recent_activity(widget_data))

        return factors

    def _extract_items(self, data: Any) -> list:
        """Extract items list from widget data (dict or pydantic model)."""
        if isinstance(data, dict):
            return data.get("items", [])
        if hasattr(data, "items") and not callable(getattr(data, "items", None)):
            return data.items
        if hasattr(data, "model_dump"):
            return data.model_dump().get("items", [])
        return []

    def _extract_total(self, data: Any) -> int:
        """Extract total count from widget data."""
        if isinstance(data, dict):
            return data.get("total", 0)
        if hasattr(data, "total") and not callable(getattr(data, "total", None)):
            return data.total
        if hasattr(data, "model_dump"):
            return data.model_dump().get("total", 0)
        return 0

    def _factors_from_decision_queue(self, data: Any) -> list[DecisionFactor]:
        factors: list[DecisionFactor] = []
        items = self._extract_items(data)
        total = self._extract_total(data)

        if total > 5:
            factors.append(DecisionFactor(
                source_layer="measurement",
                source_domain="decision_queue",
                key="high_pending_decisions",
                value=total,
                label=f"{total} pending decisions in queue",
                severity="warning",
            ))

        high_priority = sum(
            1 for item in items
            if getattr(item, "priority", None) == "high"
            or (isinstance(item, dict) and item.get("priority") == "high")
        )
        if high_priority > 0:
            factors.append(DecisionFactor(
                source_layer="measurement",
                source_domain="decision_queue",
                key="critical_decisions",
                value=high_priority,
                label=f"{high_priority} high-priority decisions pending",
                severity="critical",
            ))

        return factors

    def _factors_from_intelligence_feed(self, data: Any) -> list[DecisionFactor]:
        factors: list[DecisionFactor] = []
        items = self._extract_items(data)

        critical_signals = sum(
            1 for item in items
            if getattr(item, "severity", None) == "critical"
            or (isinstance(item, dict) and item.get("severity") == "critical")
        )
        if critical_signals > 0:
            factors.append(DecisionFactor(
                source_layer="measurement",
                source_domain="intelligence_feed",
                key="critical_signals",
                value=critical_signals,
                label=f"{critical_signals} critical intelligence signals",
                severity="critical",
            ))

        high_signals = sum(
            1 for item in items
            if getattr(item, "severity", None) == "high"
            or (isinstance(item, dict) and item.get("severity") == "high")
        )
        if high_signals > 0:
            factors.append(DecisionFactor(
                source_layer="measurement",
                source_domain="intelligence_feed",
                key="warning_signals",
                value=high_signals,
                label=f"{high_signals} high-severity intelligence signals",
                severity="warning",
            ))

        return factors

    def _factors_from_mission_center(self, data: Any) -> list[DecisionFactor]:
        factors: list[DecisionFactor] = []
        data_dict = data
        if hasattr(data, "model_dump"):
            data_dict = data.model_dump()
        elif not isinstance(data, dict):
            return factors

        active_deals = data_dict.get("activeDeals", 0)
        pipeline = data_dict.get("pipelineValue", 0)
        signals_today = data_dict.get("signalsToday", 0)

        if active_deals == 0:
            factors.append(DecisionFactor(
                source_layer="fact",
                source_domain="mission_center",
                key="no_active_deals",
                value=0,
                label="No active deals in pipeline",
                severity="warning",
            ))

        if signals_today > 10:
            factors.append(DecisionFactor(
                source_layer="measurement",
                source_domain="mission_center",
                key="high_signal_volume",
                value=signals_today,
                label=f"{signals_today} signals detected today — high activity",
                severity="info",
            ))

        return factors

    def _factors_from_recent_activity(self, data: Any) -> list[DecisionFactor]:
        factors: list[DecisionFactor] = []
        items = self._extract_items(data)

        if not items:
            factors.append(DecisionFactor(
                source_layer="measurement",
                source_domain="recent_activity",
                key="no_recent_activity",
                value=0,
                label="No recent activity",
                severity="info",
            ))

        return factors

    def _build_scored_decisions(
        self,
        factors: list[DecisionFactor],
        recommendation: Recommendation | None,
    ) -> list[dict[str, Any]]:
        """Build scored decision items from factors and optional recommendation."""
        scored: list[dict[str, Any]] = []

        for factor in factors:
            score = self._factor_to_score(factor)
            scored.append({
                "factor_key": factor.key,
                "source_domain": factor.source_domain,
                "label": factor.label,
                "severity": factor.severity,
                "score": score,
                "value": factor.value,
            })

        if recommendation:
            scored.append({
                "factor_key": "recommendation",
                "source_domain": "recommendation_engine",
                "label": recommendation.title,
                "severity": "critical",
                "score": recommendation.confidence,
                "value": recommendation.description,
            })

        return scored

    def _factor_to_score(self, factor: DecisionFactor) -> float:
        """Convert a factor's severity + value to a 0-1 score."""
        severity_weights = {"critical": 1.0, "warning": 0.7, "info": 0.3}
        base = severity_weights.get(factor.severity, 0.5)

        value = factor.value
        if isinstance(value, (int, float)) and value > 0:
            value_factor = min(value / 10.0, 1.0)
            return round((base + value_factor) / 2, 4)

        return base

    def _compute_overall_health(self, factors: list[DecisionFactor]) -> float:
        """Compute an overall dashboard health score (0 = critical, 1 = healthy)."""
        if not factors:
            return 1.0

        critical = sum(1 for f in factors if f.severity == "critical")
        warnings = sum(1 for f in factors if f.severity == "warning")
        total = len(factors)

        penalty = (critical * 0.3 + warnings * 0.1) / max(total, 1)
        return round(max(1.0 - penalty, 0.0), 4)
