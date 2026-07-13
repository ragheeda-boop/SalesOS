"""DashboardDecisionProvider — scores dashboard widget signals via Decision Platform.

Collects widget signals (from mission-center, decision-queue, intelligence-feed, etc.),
converts them to DecisionContext factors, and returns scored recommendations.

Flow: Widget Signals → DecisionContext → RecommendationEngine → Scored Decisions
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sdk.scoring.interfaces import (
    DecisionContext,
    DecisionFactor,
    DecisionServiceProtocol,
    Recommendation,
    RecommendationEngineProtocol,
)

logger = logging.getLogger(__name__)


# ── Domain context result types ────────────────────────────────────


class CompanyDecisionContext:
    """Decision context for Company Intelligence widgets."""

    def __init__(
        self,
        company_id: str,
        tenant_id: str,
        factors: list[DecisionFactor],
        recommendation: Recommendation | None,
        health_score: float,
        signals_summary: dict[str, Any],
    ):
        self.company_id = company_id
        self.tenant_id = tenant_id
        self.factors = factors
        self.recommendation = recommendation
        self.health_score = health_score
        self.signals_summary = signals_summary

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "tenant_id": self.tenant_id,
            "health_score": self.health_score,
            "factors_count": len(self.factors),
            "critical_count": sum(1 for f in self.factors if f.severity == "critical"),
            "warning_count": sum(1 for f in self.factors if f.severity == "warning"),
            "has_recommendation": self.recommendation is not None,
            "recommendation_title": self.recommendation.title if self.recommendation else None,
            "recommendation_confidence": self.recommendation.confidence if self.recommendation else None,
            "signals_summary": self.signals_summary,
        }


class RevenueDecisionContext:
    """Decision context for Revenue / Pipeline widgets."""

    def __init__(
        self,
        tenant_id: str,
        factors: list[DecisionFactor],
        recommendation: Recommendation | None,
        pipeline_health: float,
        revenue_metrics: dict[str, Any],
    ):
        self.tenant_id = tenant_id
        self.factors = factors
        self.recommendation = recommendation
        self.pipeline_health = pipeline_health
        self.revenue_metrics = revenue_metrics

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "pipeline_health": self.pipeline_health,
            "factors_count": len(self.factors),
            "critical_count": sum(1 for f in self.factors if f.severity == "critical"),
            "has_recommendation": self.recommendation is not None,
            "recommendation_title": self.recommendation.title if self.recommendation else None,
            "revenue_metrics": self.revenue_metrics,
        }


class PipelineDecisionContext:
    """Decision context for Pipeline Intelligence widgets."""

    def __init__(
        self,
        tenant_id: str,
        factors: list[DecisionFactor],
        recommendation: Recommendation | None,
        pipeline_summary: dict[str, Any],
        stage_health: dict[str, float],
    ):
        self.tenant_id = tenant_id
        self.factors = factors
        self.recommendation = recommendation
        self.pipeline_summary = pipeline_summary
        self.stage_health = stage_health

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "factors_count": len(self.factors),
            "critical_count": sum(1 for f in self.factors if f.severity == "critical"),
            "has_recommendation": self.recommendation is not None,
            "recommendation_title": self.recommendation.title if self.recommendation else None,
            "pipeline_summary": self.pipeline_summary,
            "stage_health": self.stage_health,
        }


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

    # ── Domain-specific context methods ────────────────────────────

    async def get_company_decision_context(
        self,
        tenant_id: str,
        company_id: str,
        company_data: dict[str, Any] | None = None,
    ) -> CompanyDecisionContext:
        """Build decision context for Company Intelligence widgets.

        Analyses company-level signals and returns a scored context
        with factors, recommendation, and health score.
        """
        factors: list[DecisionFactor] = []
        company_data = company_data or {}

        # Fact layer: company profile signals
        employee_count = company_data.get("employees_count", 0)
        annual_revenue = company_data.get("annual_revenue", 0)

        if employee_count and employee_count > 500:
            factors.append(DecisionFactor(
                source_layer="fact", source_domain="company",
                key="large_enterprise", value=employee_count,
                label=f"Enterprise account ({employee_count} employees)",
                severity="info",
            ))

        if annual_revenue and annual_revenue > 10_000_000:
            factors.append(DecisionFactor(
                source_layer="fact", source_domain="company",
                key="high_revenue", value=annual_revenue,
                label=f"High-revenue account (${annual_revenue:,.0f})",
                severity="info",
            ))

        # Measurement layer: engagement signals
        recent_activities = company_data.get("recent_activities", [])
        if not recent_activities:
            factors.append(DecisionFactor(
                source_layer="measurement", source_domain="company",
                key="no_engagement", value=0,
                label="No recent engagement with company",
                severity="warning",
            ))
        elif len(recent_activities) > 20:
            factors.append(DecisionFactor(
                source_layer="measurement", source_domain="company",
                key="high_engagement", value=len(recent_activities),
                label=f"High engagement ({len(recent_activities)} recent activities)",
                severity="info",
            ))

        # Knowledge layer: signals
        signals = company_data.get("signals", [])
        critical_signals = [s for s in signals if (s.get("severity") if isinstance(s, dict) else getattr(s, "severity", "")) == "critical"]
        if critical_signals:
            factors.append(DecisionFactor(
                source_layer="knowledge", source_domain="company",
                key="critical_signals", value=len(critical_signals),
                label=f"{len(critical_signals)} critical intelligence signals",
                severity="critical",
            ))

        # Score via DecisionPlatform
        recommendation = None
        health_score = self._compute_overall_health(factors)

        try:
            scored = await self.score_dashboard(tenant_id, {"company": company_data})
            if scored.get("scored_decisions"):
                top = scored["scored_decisions"][0]
                recommendation = Recommendation(
                    title=top.get("label", "Company Review"),
                    description=top.get("source_domain", ""),
                    confidence=top.get("score", 0.0),
                )
        except Exception as exc:
            logger.debug("Company context scoring failed (non-blocking): %s", exc)

        signals_summary = {
            "total": len(signals),
            "critical": len(critical_signals),
            "recent_activities": len(recent_activities),
        }

        return CompanyDecisionContext(
            company_id=company_id,
            tenant_id=tenant_id,
            factors=factors,
            recommendation=recommendation,
            health_score=health_score,
            signals_summary=signals_summary,
        )

    async def get_revenue_decision_context(
        self,
        tenant_id: str,
        revenue_data: dict[str, Any] | None = None,
    ) -> RevenueDecisionContext:
        """Build decision context for Revenue widgets.

        Analyses pipeline value, forecast accuracy, and deal stages
        to produce a revenue-focused decision context.
        """
        revenue_data = revenue_data or {}
        factors: list[DecisionFactor] = []

        pipeline_value = revenue_data.get("pipeline_value", 0)
        forecast_value = revenue_data.get("forecast_value", 0)
        won_value = revenue_data.get("won_value", 0)
        lost_value = revenue_data.get("lost_value", 0)
        total_deals = revenue_data.get("total_deals", 0)
        win_rate = revenue_data.get("win_rate", 0)

        # Forecast accuracy
        if forecast_value > 0 and pipeline_value > 0:
            coverage = pipeline_value / max(forecast_value, 1)
            if coverage < 2.0:
                factors.append(DecisionFactor(
                    source_layer="measurement", source_domain="revenue",
                    key="low_coverage", value=round(coverage, 2),
                    label=f"Low pipeline coverage ({coverage:.1f}x forecast)",
                    severity="warning",
                ))
            elif coverage > 4.0:
                factors.append(DecisionFactor(
                    source_layer="measurement", source_domain="revenue",
                    key="high_coverage", value=round(coverage, 2),
                    label=f"Healthy pipeline coverage ({coverage:.1f}x)",
                    severity="info",
                ))

        # Win rate
        if win_rate > 0 and win_rate < 0.20:
            factors.append(DecisionFactor(
                source_layer="measurement", source_domain="revenue",
                key="low_win_rate", value=win_rate,
                label=f"Low win rate ({win_rate:.0%})",
                severity="critical",
            ))
        elif win_rate >= 0.30:
            factors.append(DecisionFactor(
                source_layer="measurement", source_domain="revenue",
                key="healthy_win_rate", value=win_rate,
                label=f"Healthy win rate ({win_rate:.0%})",
                severity="info",
            ))

        # Revenue loss
        if lost_value > won_value and lost_value > 0:
            factors.append(DecisionFactor(
                source_layer="measurement", source_domain="revenue",
                key="revenue_leakage", value=lost_value,
                label=f"Revenue leakage: ${lost_value:,.0f} lost vs ${won_value:,.0f} won",
                severity="critical",
            ))

        # Large deal concentration
        large_deals = revenue_data.get("large_deals", [])
        if large_deals and total_deals:
            concentration = len(large_deals) / max(total_deals, 1)
            if concentration > 0.5:
                factors.append(DecisionFactor(
                    source_layer="measurement", source_domain="revenue",
                    key="deal_concentration", value=concentration,
                    label=f"High deal concentration ({concentration:.0%} in large deals)",
                    severity="warning",
                ))

        recommendation = None
        pipeline_health = self._compute_overall_health(factors)

        try:
            scored = await self.score_dashboard(tenant_id, {"revenue": revenue_data})
            if scored.get("scored_decisions"):
                top = scored["scored_decisions"][0]
                recommendation = Recommendation(
                    title=top.get("label", "Revenue Review"),
                    description=top.get("source_domain", ""),
                    confidence=top.get("score", 0.0),
                )
        except Exception as exc:
            logger.debug("Revenue context scoring failed (non-blocking): %s", exc)

        revenue_metrics = {
            "pipeline_value": pipeline_value,
            "forecast_value": forecast_value,
            "won_value": won_value,
            "lost_value": lost_value,
            "total_deals": total_deals,
            "win_rate": win_rate,
        }

        return RevenueDecisionContext(
            tenant_id=tenant_id,
            factors=factors,
            recommendation=recommendation,
            pipeline_health=pipeline_health,
            revenue_metrics=revenue_metrics,
        )

    async def get_pipeline_decision_context(
        self,
        tenant_id: str,
        pipeline_data: dict[str, Any] | None = None,
    ) -> PipelineDecisionContext:
        """Build decision context for Pipeline Intelligence widgets.

        Analyses pipeline stage distribution, stagnation, and velocity
        to produce pipeline-focused decision context.
        """
        pipeline_data = pipeline_data or {}
        factors: list[DecisionFactor] = []

        stages = pipeline_data.get("stages", {})
        total_value = pipeline_data.get("total_value", 0)
        total_count = pipeline_data.get("total_count", 0)
        avg_age_days = pipeline_data.get("avg_age_days", 0)

        # Stage health: detect bottlenecks
        stage_health: dict[str, float] = {}
        for stage_name, stage_data in stages.items():
            if isinstance(stage_data, dict):
                count = stage_data.get("count", 0)
                value = stage_data.get("value", 0)
                aging = stage_data.get("avg_days_in_stage", 0)
            else:
                count = getattr(stage_data, "count", 0)
                value = getattr(stage_data, "value", 0)
                aging = getattr(stage_data, "avg_days_in_stage", 0)

            health = 1.0
            if aging > 30:
                health = max(0.0, 1.0 - (aging - 30) / 60)
                factors.append(DecisionFactor(
                    source_layer="measurement", source_domain="pipeline",
                    key=f"stage_aging_{stage_name}", value=aging,
                    label=f"Stage '{stage_name}' aging: {aging} days avg",
                    severity="critical" if aging > 60 else "warning",
                ))
            elif aging > 14:
                health = max(0.0, 1.0 - (aging - 14) / 30)

            stage_health[stage_name] = round(health, 2)

        # Stagnant deals
        stalled = pipeline_data.get("stalled_deals", 0)
        if stalled > 0:
            factors.append(DecisionFactor(
                source_layer="measurement", source_domain="pipeline",
                key="stalled_pipeline", value=stalled,
                label=f"{stalled} deals stalled (no activity >14 days)",
                severity="critical" if stalled > 5 else "warning",
            ))

        # Pipeline velocity
        velocity = pipeline_data.get("velocity", 0)
        if velocity and velocity < 0.5:
            factors.append(DecisionFactor(
                source_layer="measurement", source_domain="pipeline",
                key="low_velocity", value=velocity,
                label=f"Low pipeline velocity ({velocity:.1f} deals/week)",
                severity="warning",
            ))

        # Empty pipeline
        if total_count == 0:
            factors.append(DecisionFactor(
                source_layer="fact", source_domain="pipeline",
                key="empty_pipeline", value=0,
                label="Pipeline is empty — no active opportunities",
                severity="critical",
            ))

        recommendation = None
        pipeline_health = self._compute_overall_health(factors)

        try:
            scored = await self.score_dashboard(tenant_id, {"pipeline": pipeline_data})
            if scored.get("scored_decisions"):
                top = scored["scored_decisions"][0]
                recommendation = Recommendation(
                    title=top.get("label", "Pipeline Review"),
                    description=top.get("source_domain", ""),
                    confidence=top.get("score", 0.0),
                )
        except Exception as exc:
            logger.debug("Pipeline context scoring failed (non-blocking): %s", exc)

        pipeline_summary = {
            "total_value": total_value,
            "total_count": total_count,
            "avg_age_days": avg_age_days,
            "stalled_deals": stalled,
            "velocity": velocity,
        }

        return PipelineDecisionContext(
            tenant_id=tenant_id,
            factors=factors,
            recommendation=recommendation,
            pipeline_summary=pipeline_summary,
            stage_health=stage_health,
        )
