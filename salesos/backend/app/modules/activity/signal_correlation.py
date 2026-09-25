"""Explainable link between activity events and commercial signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Iterable


@dataclass(frozen=True)
class CorrelatedSignal:
    activity_id: str
    signal_id: str
    relation: str
    confidence: float
    observed_at: datetime


def correlate_activity_signals(
    activities: Iterable[dict[str, object]],
    signals: Iterable[dict[str, object]],
    *,
    window: timedelta = timedelta(days=14),
) -> list[CorrelatedSignal]:
    output: list[CorrelatedSignal] = []
    for activity in activities:
        company_id = str(activity.get("company_id") or "")
        activity_id = str(activity.get("id") or "")
        at = activity.get("occurred_at")
        if not company_id or not activity_id or not isinstance(at, datetime):
            continue
        at = at if at.tzinfo and at.utcoffset() else at.replace(tzinfo=UTC)
        for signal in signals:
            if str(signal.get("company_id") or "") != company_id:
                continue
            signal_at = signal.get("observed_at")
            signal_id = str(signal.get("id") or "")
            if not signal_id or not isinstance(signal_at, datetime):
                continue
            signal_at = signal_at if signal_at.tzinfo and signal_at.utcoffset() else signal_at.replace(tzinfo=UTC)
            if abs(signal_at.astimezone(UTC) - at.astimezone(UTC)) <= window:
                output.append(CorrelatedSignal(activity_id, signal_id, "same_company_time_window", 0.7, signal_at.astimezone(UTC)))
    return output
