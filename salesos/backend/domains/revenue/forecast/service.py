from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import ForecastSnapshot, ForecastSnapshotStatus
from .repo import ForecastKPIs, ForecastRepository
from .engine import CommercialInput, ForecastEngine


class ForecastService:
    """ForecastService — creates immutable snapshots, never writes to commercial domains."""

    def __init__(self, repository: ForecastRepository, engine: ForecastEngine | None = None, event_bus: Any = None):
        self._repository = repository
        self._engine = engine or ForecastEngine()
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus: return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id, aggregate_id=data.get("snapshot_id", ""), data=data)
        event.event_type = event_type; await self._event_bus.publish(event)

    async def create_forecast(
        self,
        tenant_id: str,
        inputs: list[CommercialInput],
        horizon_months: int = 3,
        title: str = "",
    ) -> ForecastSnapshot:
        snapshot = self._engine.predict(inputs, horizon_months)
        snapshot.tenant_id = tenant_id
        snapshot.title = title or f"Forecast — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        result = await self._repository.save(snapshot)
        await self._emit("forecast.created", tenant_id, {
            "snapshot_id": snapshot.id,
            "total_expected": snapshot.total_expected_revenue,
            "total_weighted": snapshot.total_weighted_revenue,
            "confidence": snapshot.overall_confidence,
        })
        return result

    async def finalize(self, snapshot_id: str) -> ForecastSnapshot:
        snapshot = await self._repository.get(snapshot_id)
        if not snapshot: raise ValueError(f"Snapshot {snapshot_id} not found")
        snapshot.status = ForecastSnapshotStatus.FINALIZED
        snapshot.finalized_at = datetime.now(timezone.utc)
        result = await self._repository.save(snapshot)
        await self._emit("forecast.finalized", snapshot.tenant_id, {"snapshot_id": snapshot_id})
        return result

    async def get(self, snapshot_id: str) -> ForecastSnapshot | None:
        return await self._repository.get(snapshot_id)

    async def get_latest(self, tenant_id: str) -> ForecastSnapshot | None:
        return await self._repository.get_latest(tenant_id)

    async def list_snapshots(self, tenant_id: str, limit: int = 10) -> list[ForecastSnapshot]:
        return await self._repository.list_by_tenant(tenant_id, limit)

    async def kpis(self, tenant_id: str) -> ForecastKPIs:
        return await self._repository.kpis(tenant_id)

    def explain(self, snapshot: ForecastSnapshot) -> list[dict]:
        """Return human-readable explanations for the forecast."""
        result = []
        for line in snapshot.lines:
            factors = [{"factor": e.factor, "value": e.value, "label": e.label, "source": f"{e.source_type}/{e.source_id}"} for e in line.explanations]
            result.append({
                "scenario": line.scenario.value,
                "expected_revenue": line.expected_revenue,
                "confidence": line.confidence,
                "risk": line.risk,
                "weighted_revenue": line.weighted_revenue,
                "source_id": line.source_id,
                "explanations": factors,
            })
        return result
