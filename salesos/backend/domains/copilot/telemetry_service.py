"""Tool telemetry service — logs every copilot tool call.

Provides in-memory storage with aggregation for success rate,
latency percentiles, result count distribution, and volume over time.
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from domains.copilot.models import ToolCallRecord, ToolTelemetryStats

logger = logging.getLogger(__name__)


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Calculate percentile from a sorted list."""
    if not sorted_values:
        return 0.0
    idx = int(math.ceil(pct / 100.0 * len(sorted_values))) - 1
    idx = max(0, min(idx, len(sorted_values) - 1))
    return sorted_values[idx]


class ToolTelemetryService:
    """In-memory telemetry for copilot tool calls."""

    def __init__(self) -> None:
        self._records: list[ToolCallRecord] = []

    def log(
        self,
        *,
        tool_name: str,
        conversation_id: str = "",
        user_id: str = "",
        tenant_id: str = "",
        success: bool,
        latency_ms: float,
        result_count: int = 0,
        error_message: str | None = None,
        input_params: dict | None = None,
    ) -> ToolCallRecord:
        record = ToolCallRecord(
            tool_name=tool_name,
            conversation_id=conversation_id,
            user_id=user_id,
            tenant_id=tenant_id,
            success=success,
            latency_ms=latency_ms,
            result_count=result_count,
            error_message=error_message,
            input_params=input_params or {},
        )
        self._records.append(record)
        return record

    def get_stats(
        self,
        tool_name: str | None = None,
        tenant_id: str | None = None,
        period_hours: float = 24.0,
    ) -> ToolTelemetryStats:
        cutoff = datetime.now(UTC) - timedelta(hours=period_hours)
        records = [
            r for r in self._records
            if r.timestamp >= cutoff
        ]
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        if tool_name:
            records = [r for r in records if r.tool_name == tool_name]

        if not records:
            return ToolTelemetryStats(
                tool_name=tool_name or "overall",
                period_hours=period_hours,
            )

        total = len(records)
        success = sum(1 for r in records if r.success)
        failures = total - success
        latencies = sorted(r.latency_ms for r in records)
        result_counts = sorted(r.result_count for r in records)

        return ToolTelemetryStats(
            tool_name=tool_name or "overall",
            total_calls=total,
            success_count=success,
            failure_count=failures,
            success_rate=round(success / total, 4) if total else 0.0,
            latency_p50_ms=round(_percentile(latencies, 50), 2),
            latency_p95_ms=round(_percentile(latencies, 95), 2),
            latency_p99_ms=round(_percentile(latencies, 99), 2),
            latency_avg_ms=round(sum(latencies) / total, 2),
            result_count_avg=round(sum(result_counts) / total, 2) if total else 0.0,
            result_count_p50=round(_percentile(result_counts, 50), 2),
            calls_per_hour=round(total / period_hours, 2) if period_hours > 0 else 0.0,
            period_hours=period_hours,
        )

    def get_tool_breakdown(
        self,
        tenant_id: str | None = None,
        period_hours: float = 24.0,
    ) -> dict[str, ToolTelemetryStats]:
        cutoff = datetime.now(UTC) - timedelta(hours=period_hours)
        records = [
            r for r in self._records
            if r.timestamp >= cutoff
        ]
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]

        tool_names = {r.tool_name for r in records}
        return {
            name: self.get_stats(tool_name=name, tenant_id=tenant_id, period_hours=period_hours)
            for name in tool_names
        }

    def get_volume_over_time(
        self,
        tool_name: str | None = None,
        tenant_id: str | None = None,
        period_hours: float = 24.0,
        bucket_minutes: int = 60,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(UTC) - timedelta(hours=period_hours)
        records = [
            r for r in self._records
            if r.timestamp >= cutoff
        ]
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        if tool_name:
            records = [r for r in records if r.tool_name == tool_name]

        if not records:
            return []

        buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "success": 0,
            "failure": 0,
        })

        for r in records:
            bucket_key = r.timestamp.strftime("%Y-%m-%dT%H:")
            minute_group = (r.timestamp.minute // bucket_minutes) * bucket_minutes
            bucket_key = f"{r.timestamp.strftime('%Y-%m-%dT%H')}:{minute_group:02d}"
            buckets[bucket_key]["count"] += 1
            if r.success:
                buckets[bucket_key]["success"] += 1
            else:
                buckets[bucket_key]["failure"] += 1

        result = []
        for key in sorted(buckets.keys()):
            entry = buckets[key]
            result.append({
                "timestamp": key,
                "total": entry["count"],
                "success": entry["success"],
                "failure": entry["failure"],
            })
        return result

    def count(
        self,
        tool_name: str | None = None,
        tenant_id: str | None = None,
    ) -> int:
        records = self._records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        if tool_name:
            records = [r for r in records if r.tool_name == tool_name]
        return len(records)
