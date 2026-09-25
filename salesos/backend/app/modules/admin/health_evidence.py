"""Honest Customer Health evidence envelope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class HealthEvidence:
    score: float
    status: str
    calculated_at: datetime
    source_metrics: dict[str, Any]
    freshness: str


def build_health_evidence(
    *, score: float, status: str, calculated_at: datetime, source_metrics: dict[str, Any],
    now: datetime | None = None, stale_after: timedelta = timedelta(hours=24),
) -> HealthEvidence:
    point = now or datetime.now(UTC)
    calculated = calculated_at if calculated_at.tzinfo and calculated_at.utcoffset() else calculated_at.replace(tzinfo=UTC)
    age = point.astimezone(UTC) - calculated.astimezone(UTC)
    freshness = "FUTURE" if age < timedelta(0) else "FRESH" if age <= stale_after else "STALE"
    return HealthEvidence(
        score=max(0.0, min(1.0, float(score))),
        status=status,
        calculated_at=calculated.astimezone(UTC),
        source_metrics=dict(source_metrics),
        freshness=freshness,
    )
