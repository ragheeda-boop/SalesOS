"""Decision Widget Registry — tracks which widgets consume DecisionProvider data.

Provides:
  - Registration of decision-enabled widgets
  - Health checks per widget
  - Adoption metrics for admin reporting
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


logger = logging.getLogger(__name__)


class WidgetDecisionStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    ERROR = "error"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass
class WidgetDecisionEntry:
    """Tracks a single widget's DecisionProvider adoption status."""
    widget_id: str
    widget_name: str
    decision_context_type: str  # "company", "revenue", "pipeline", "dashboard"
    uses_decision_provider: bool = True
    uses_nba_feed: bool = False
    last_scored_at: Optional[datetime] = None
    last_health_score: Optional[float] = None
    consecutive_failures: int = 0
    status: WidgetDecisionStatus = WidgetDecisionStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "widget_id": self.widget_id,
            "widget_name": self.widget_name,
            "decision_context_type": self.decision_context_type,
            "uses_decision_provider": self.uses_decision_provider,
            "uses_nba_feed": self.uses_nba_feed,
            "last_scored_at": self.last_scored_at.isoformat() if self.last_scored_at else None,
            "last_health_score": self.last_health_score,
            "consecutive_failures": self.consecutive_failures,
            "status": self.status.value,
            "metadata": self.metadata,
        }


class DecisionWidgetRegistry:
    """Central registry for decision-enabled widgets.

    Tracks adoption, health, and provides metrics for admin endpoints.
    Thread-safe: uses plain dict (single-process FastAPI assumed).
    """

    _instance: Optional["DecisionWidgetRegistry"] = None

    def __init__(self):
        self._widgets: dict[str, WidgetDecisionEntry] = {}
        self._health_checkers: dict[str, Callable[[], bool]] = {}
        self._created_at = datetime.now(timezone.utc)

    @classmethod
    def get_instance(cls) -> "DecisionWidgetRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    # ── Registration ───────────────────────────────────────────

    def register(
        self,
        widget_id: str,
        widget_name: str,
        decision_context_type: str = "dashboard",
        uses_nba_feed: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> WidgetDecisionEntry:
        """Register a widget as decision-enabled."""
        entry = WidgetDecisionEntry(
            widget_id=widget_id,
            widget_name=widget_name,
            decision_context_type=decision_context_type,
            uses_nba_feed=uses_nba_feed,
            metadata=metadata or {},
        )
        self._widgets[widget_id] = entry
        logger.info(
            "DecisionWidgetRegistry: registered widget '%s' (%s, context=%s)",
            widget_id, widget_name, decision_context_type,
        )
        return entry

    def unregister(self, widget_id: str) -> bool:
        """Remove a widget from the registry."""
        if widget_id in self._widgets:
            del self._widgets[widget_id]
            self._health_checkers.pop(widget_id, None)
            logger.info("DecisionWidgetRegistry: unregistered widget '%s'", widget_id)
            return True
        return False

    def get(self, widget_id: str) -> WidgetDecisionEntry | None:
        return self._widgets.get(widget_id)

    def list_all(self) -> list[WidgetDecisionEntry]:
        return list(self._widgets.values())

    # ── Health checks ──────────────────────────────────────────

    def set_health_check(self, widget_id: str, checker: Callable[[], bool]) -> None:
        """Register a health check function for a widget."""
        self._health_checkers[widget_id] = checker

    def run_health_checks(self) -> dict[str, WidgetDecisionStatus]:
        """Run all registered health checks and update widget statuses."""
        results: dict[str, WidgetDecisionStatus] = {}
        for widget_id, entry in self._widgets.items():
            checker = self._health_checkers.get(widget_id)
            if checker is None:
                entry.status = WidgetDecisionStatus.UNKNOWN
                results[widget_id] = WidgetDecisionStatus.UNKNOWN
                continue
            try:
                ok = checker()
                if ok:
                    entry.status = WidgetDecisionStatus.ACTIVE
                    entry.consecutive_failures = 0
                else:
                    entry.consecutive_failures += 1
                    entry.status = (
                        WidgetDecisionStatus.DEGRADED
                        if entry.consecutive_failures < 3
                        else WidgetDecisionStatus.ERROR
                    )
            except Exception:
                entry.consecutive_failures += 1
                entry.status = WidgetDecisionStatus.ERROR
            results[widget_id] = entry.status
        return results

    # ── Lifecycle events ───────────────────────────────────────

    def record_scored(self, widget_id: str, health_score: float) -> None:
        """Record that a widget was successfully scored by DecisionProvider."""
        entry = self._widgets.get(widget_id)
        if entry:
            entry.last_scored_at = datetime.now(timezone.utc)
            entry.last_health_score = health_score
            entry.consecutive_failures = 0
            entry.status = WidgetDecisionStatus.ACTIVE

    def record_failure(self, widget_id: str) -> None:
        """Record that a widget's decision scoring failed."""
        entry = self._widgets.get(widget_id)
        if entry:
            entry.consecutive_failures += 1
            entry.status = (
                WidgetDecisionStatus.DEGRADED
                if entry.consecutive_failures < 3
                else WidgetDecisionStatus.ERROR
            )

    # ── Metrics ────────────────────────────────────────────────

    def get_adoption_metrics(self) -> dict[str, Any]:
        """Return adoption metrics for admin reporting."""
        all_widgets = list(self._widgets.values())
        total = len(all_widgets)
        using_dp = sum(1 for w in all_widgets if w.uses_decision_provider)
        using_nba = sum(1 for w in all_widgets if w.uses_nba_feed)
        active = sum(1 for w in all_widgets if w.status == WidgetDecisionStatus.ACTIVE)
        degraded = sum(1 for w in all_widgets if w.status == WidgetDecisionStatus.DEGRADED)
        error = sum(1 for w in all_widgets if w.status == WidgetDecisionStatus.ERROR)

        return {
            "total_widgets": total,
            "using_decision_provider": using_dp,
            "using_nba_feed": using_nba,
            "adoption_percentage": round(using_dp / max(total, 1) * 100, 1),
            "health": {
                "active": active,
                "degraded": degraded,
                "error": error,
            },
            "registered_at": self._created_at.isoformat(),
            "widgets": [w.to_dict() for w in all_widgets],
        }


def register_default_widgets() -> None:
    """Register the built-in dashboard widgets in the Decision Registry."""
    registry = DecisionWidgetRegistry.get_instance()

    defaults = [
        ("missionCenter", "Mission Center", "dashboard", False),
        ("decisionQueue", "Decision Queue", "dashboard", True),
        ("intelligenceFeed", "Intelligence Feed", "company", False),
        ("aiBrief", "AI Brief", "dashboard", False),
        ("marketPulse", "Market Pulse", "revenue", False),
        ("recentActivity", "Recent Activity", "dashboard", False),
    ]

    for widget_id, name, ctx_type, uses_nba in defaults:
        if not registry.get(widget_id):
            registry.register(
                widget_id=widget_id,
                widget_name=name,
                decision_context_type=ctx_type,
                uses_nba_feed=uses_nba,
            )
