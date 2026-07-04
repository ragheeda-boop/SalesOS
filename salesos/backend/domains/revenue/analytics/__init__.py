"""Revenue Analytics Domain — Measurement Layer.

Owns KPIs, never facts or decisions.
Snapshot-based, immutable, explainable, drill-down to RTI.
"""

from .models import AnalyticsSnapshot, KPI, KPIValue, MetricCategory
from .registry import KPIRegistry
from .repo import AnalyticsRepository
from .service import AnalyticsService

__all__ = ["AnalyticsSnapshot", "KPI", "KPIValue", "MetricCategory", "KPIRegistry", "AnalyticsRepository", "AnalyticsService"]
