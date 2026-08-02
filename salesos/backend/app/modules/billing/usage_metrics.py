"""STORY-05-03 — UsageMeter metric keys + hour bucketing (pure).

OBJ-324 dimensions: seats, AI tokens, connector syncs, storage (+ api_calls).
Hourly rollup granularity per PROGRAM_PLAN / Sprint-06. No Stripe secrets.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum


class UsageMetricKey(StrEnum):
    SEATS = "seats"
    AI_TOKENS = "ai_tokens"
    CONNECTOR_SYNCS = "connector_syncs"
    API_CALLS = "api_calls"
    STORAGE_MB = "storage_mb"


class UsageOp(StrEnum):
    """``add`` sums in rollup; ``set`` takes MAX (gauges like seats/storage)."""

    ADD = "add"
    SET = "set"


METRIC_KEYS = frozenset(m.value for m in UsageMetricKey)
# Gauges default to set; counters to add — callers may override.
DEFAULT_OP: dict[str, UsageOp] = {
    UsageMetricKey.SEATS.value: UsageOp.SET,
    UsageMetricKey.STORAGE_MB.value: UsageOp.SET,
    UsageMetricKey.AI_TOKENS.value: UsageOp.ADD,
    UsageMetricKey.CONNECTOR_SYNCS.value: UsageOp.ADD,
    UsageMetricKey.API_CALLS.value: UsageOp.ADD,
}


def normalize_metric_key(key: str) -> str:
    k = (key or "").strip().lower()
    if k not in METRIC_KEYS:
        raise ValueError(f"unknown metric_key: {key!r}; expected one of {sorted(METRIC_KEYS)}")
    return k


def normalize_op(op: str | None, *, metric_key: str) -> str:
    if op is None or not str(op).strip():
        return DEFAULT_OP[metric_key].value
    o = str(op).strip().lower()
    if o not in {UsageOp.ADD.value, UsageOp.SET.value}:
        raise ValueError("op must be 'add' or 'set'")
    return o


def hour_bucket(at: datetime) -> tuple[datetime, datetime]:
    """Return [period_start, period_end) for the UTC hour containing ``at``."""
    at = at.replace(tzinfo=UTC) if at.tzinfo is None else at.astimezone(UTC)
    start = at.replace(minute=0, second=0, microsecond=0)
    return start, start + timedelta(hours=1)


def combine_quantities(op: str, current: float, incoming: float) -> float:
    if op == UsageOp.SET.value:
        return max(float(current), float(incoming))
    return float(current) + float(incoming)
