"""Engagement Engine — Plugin-based engagement metrics (ADR-012 §14).

Each metric is a plugin implementing MetricPlugin. The engine registers
plugins and computes all metrics for a given context.

Built-in metrics (13 plugins):
  email_count_sent, email_count_received, reply_rate, meeting_count,
  meeting_hours, meeting_completion_rate, last_email, last_meeting,
  last_activity, communication_velocity, response_time_avg,
  followup_delay, relationship_health
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MetricContext:
    company_id: str
    tenant_id: str
    since: datetime
    until: datetime


@dataclass
class MetricValue:
    plugin_id: str
    value: float | int | str | None
    unit: str  # "count", "percent", "hours", "days", "score"
    label: str
    confidence: float = 1.0  # 0.0–1.0
    metadata: dict = field(default_factory=dict)


class MetricPlugin(ABC):
    """Single engagement metric, independently testable."""

    id: str = ""
    label: str = ""
    label_ar: str = ""
    category: str = ""  # "email", "meeting", "communication", "composite"

    @abstractmethod
    async def compute(self, ctx: MetricContext) -> MetricValue: ...


class EngagementEngine:
    """Computes all registered engagement metrics for a company."""

    def __init__(self, email_engine=None, calendar_engine=None, activity_reader=None):
        self._plugins: dict[str, MetricPlugin] = {}
        self._email_engine = email_engine
        self._calendar_engine = calendar_engine
        self._activity_reader = activity_reader

    def register(self, plugin: MetricPlugin) -> None:
        """Register a metric plugin."""
        self._plugins[plugin.id] = plugin

    def unregister(self, plugin_id: str) -> None:
        """Remove a metric plugin."""
        self._plugins.pop(plugin_id, None)

    @property
    def plugins(self) -> dict[str, MetricPlugin]:
        return dict(self._plugins)

    async def compute_all(self, ctx: MetricContext) -> dict[str, MetricValue]:
        """Compute every registered plugin for the given context."""
        results: dict[str, MetricValue] = {}
        for pid, plugin in self._plugins.items():
            try:
                results[pid] = await plugin.compute(ctx)
            except Exception as e:
                results[pid] = MetricValue(
                    plugin_id=pid,
                    value=None,
                    unit="error",
                    label=plugin.label,
                    confidence=0.0,
                    metadata={"error": str(e)},
                )
        return results

    async def compute(
        self, ctx: MetricContext, plugin_ids: list[str]
    ) -> dict[str, MetricValue]:
        """Compute specific plugins for company context."""
        results: dict[str, MetricValue] = {}
        for pid in plugin_ids:
            plugin = self._plugins.get(pid)
            if plugin:
                try:
                    results[pid] = await plugin.compute(ctx)
                except Exception as e:
                    results[pid] = MetricValue(
                        plugin_id=pid,
                        value=None,
                        unit="error",
                        label=plugin.label if plugin else pid,
                        confidence=0.0,
                        metadata={"error": str(e)},
                    )
        return results

    async def get_relationship_health(
        self, company_id: str, tenant_id: str
    ) -> dict:
        """Compute all metrics and return relationship health score."""
        ctx = MetricContext(
            company_id=company_id,
            tenant_id=tenant_id,
            since=datetime(2020, 1, 1, tzinfo=timezone.utc),
            until=datetime.now(timezone.utc),
        )
        metrics = await self.compute_all(ctx)

        health_score = self._calculate_health_score(metrics)

        return {
            "company_id": company_id,
            "relationship_health": health_score,
            "metrics": {
                pid: {"value": mv.value, "unit": mv.unit}
                for pid, mv in metrics.items()
            },
        }

    @staticmethod
    def _calculate_health_score(metrics: dict[str, MetricValue]) -> float:
        """Calculate composite relationship health from all metrics.

        Weighted average of: recency, frequency, reply_rate, meeting_consistency.
        """
        weights = {
            "reply_rate": 0.25,
            "communication_velocity": 0.20,
            "last_activity": 0.20,
            "meeting_count": 0.15,
            "email_count_sent": 0.10,
            "meeting_completion_rate": 0.10,
        }
        score = 0.0
        total_weight = 0.0

        for pid, weight in weights.items():
            mv = metrics.get(pid)
            if mv and mv.value is not None:
                normalized = EngagementEngine._normalize(mv)
                score += normalized * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0
        return round(score / total_weight, 4)

    @staticmethod
    def _normalize(mv: MetricValue) -> float:
        """Normalize a metric value to 0.0–1.0 range."""
        if mv.value is None:
            return 0.0

        value = float(mv.value)

        if mv.unit == "percent":
            return min(value, 1.0)

        if mv.unit == "days":
            # Fewer days since last activity = better health
            # 0 days = 1.0, 365+ days = 0.0
            return max(0.0, 1.0 - (value / 365.0))

        if mv.unit == "count":
            if mv.plugin_id in ("email_count_sent", "email_count_received"):
                return min(value / 100.0, 1.0)
            if mv.plugin_id == "meeting_count":
                return min(value / 20.0, 1.0)
            return min(value / 50.0, 1.0)

        if mv.unit == "hours":
            return 1.0 - min(value / 40.0, 1.0)

        if mv.unit == "score":
            return min(max(value, 0.0), 1.0)

        return 0.5
