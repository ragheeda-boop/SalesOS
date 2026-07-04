"""Forecast Domain — Projection Engine, not System of Record.

Owns predictions, never facts. Immutable snapshots.
Every prediction must be explainable, reproducible, and traceable to commercial facts.
"""

from .models import (
    ForecastExplanation, ForecastLine, ForecastScenario,
    ForecastSnapshot, ForecastSnapshotStatus,
)
from .repo import ForecastRepository
from .engine import ForecastEngine
from .service import ForecastService

__all__ = [
    "ForecastExplanation", "ForecastLine", "ForecastScenario",
    "ForecastSnapshot", "ForecastSnapshotStatus",
    "ForecastRepository", "ForecastEngine", "ForecastService",
]
