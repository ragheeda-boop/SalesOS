"""STORY-08-03 — Drift-detection job (fields_get()-equivalent check).

Produces loud structured alerts when mapped fields disappear/rename.
No network I/O here — caller supplies remote schema snapshot.
Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from app.modules.integration_hub.field_mapping import (
    DriftAlert,
    FieldMapEntry,
    detect_field_drift,
    parse_field_mappings,
)


@dataclass(frozen=True)
class DriftJobResult:
    status: str  # ok | alert
    alert_count: int
    critical_count: int
    alerts: tuple[DriftAlert, ...]
    model: str
    connection_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "alert_count": self.alert_count,
            "critical_count": self.critical_count,
            "model": self.model,
            "connection_id": self.connection_id,
            "alerts": [asdict(a) for a in self.alerts],
        }


def run_field_drift_job(
    *,
    model: str,
    mappings: tuple[FieldMapEntry, ...] | list[FieldMapEntry] | list[dict[str, Any]],
    remote_schema: Mapping[str, Any],
    baseline_fields: set[str] | frozenset[str] | None = None,
    connection_id: str | None = None,
) -> DriftJobResult:
    """Run one drift check; status=alert when any critical finding exists."""
    model_key = (model or "").strip()
    if not model_key:
        raise ValueError("model is required")
    if mappings and isinstance(mappings[0], dict):
        entries = parse_field_mappings(mappings)
    else:
        entries = tuple(mappings)  # type: ignore[arg-type]
    alerts = detect_field_drift(
        mappings=entries,
        remote_schema=remote_schema,
        baseline_fields=baseline_fields,
    )
    critical = sum(1 for a in alerts if a.severity == "critical")
    # Warnings alone stay status=ok (surfaced in alerts); critical → alert.
    status = "alert" if critical else "ok"
    return DriftJobResult(
        status=status,
        alert_count=len(alerts),
        critical_count=critical,
        alerts=tuple(alerts),
        model=model_key,
        connection_id=connection_id,
    )
