"""Connector health and replay posture shared by Integration Hub adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable


@dataclass(frozen=True)
class ConnectorHealth:
    connector_key: str
    last_success_at: datetime | None
    failed_runs: int
    dead_letters: int
    retryable: bool

    @property
    def status(self) -> str:
        if self.dead_letters > 0:
            return "blocked"
        if self.failed_runs > 0:
            return "degraded"
        if self.last_success_at is None:
            return "unknown"
        return "healthy"


def summarize_connector_health(rows: Iterable[ConnectorHealth]) -> dict[str, object]:
    items = list(rows)
    counts = {state: 0 for state in ("healthy", "degraded", "blocked", "unknown")}
    for row in items:
        counts[row.status] += 1
    return {
        "connectors": [
            {
                "connector_key": row.connector_key,
                "status": row.status,
                "failed_runs": row.failed_runs,
                "dead_letters": row.dead_letters,
                "retryable": row.retryable,
                "last_success_at": row.last_success_at.astimezone(UTC).isoformat()
                if row.last_success_at
                else None,
            }
            for row in items
        ],
        "counts": counts,
        "action_required": any(row.status in {"blocked", "degraded"} for row in items),
    }
