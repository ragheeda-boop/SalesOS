from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .models import AnalyticsSnapshot, KPIValue, MetricCategory
from .registry import KPIRegistry
from .repo import AnalyticsRepository


@dataclass
class AnalyticsInput:
    """Input data consumed by Analytics — never stored."""
    total_booked_revenue: float = 0.0
    total_expected_revenue: float = 0.0
    previous_booked_revenue: float = 0.0
    pipeline_coverage_ratio: float = 0.0
    avg_stage_velocity_days: float = 0.0
    stage_conversion_rate: float = 0.0
    stage_aging_percent: float = 0.0
    quote_acceptance_rate: float = 0.0
    avg_discount_percent: float = 0.0
    avg_approval_time_days: float = 0.0
    contract_renewal_rate: float = 0.0
    contract_expansion_rate: float = 0.0
    forecast_accuracy: float = 0.0
    forecast_bias: float = 0.0
    forecast_stability: float = 0.0
    activity_sla_compliance: float = 0.0
    rep_productivity: float = 0.0



class AnalyticsService:
    """Produces immutable measurement snapshots. Never creates facts or decisions."""

    def __init__(self, repository: AnalyticsRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus
        KPIRegistry.load_defaults()

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus: return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id, aggregate_id=data.get("snapshot_id", ""), data=data)
        event.event_type = event_type; await self._event_bus.publish(event)

    async def generate_snapshot(self, tenant_id: str, inputs: AnalyticsInput, period_start: datetime, period_end: datetime) -> AnalyticsSnapshot:
        values: list[KPIValue] = []

        # ── Revenue KPIs ──
        values.append(self._kpi("booked_revenue", inputs.total_booked_revenue, inputs.previous_booked_revenue))
        values.append(self._kpi("expected_revenue", inputs.total_expected_revenue))
        growth = ((inputs.total_booked_revenue - inputs.previous_booked_revenue) / inputs.previous_booked_revenue * 100) if inputs.previous_booked_revenue > 0 else 0.0
        values.append(self._kpi("revenue_growth", growth))
        variance = abs(inputs.total_expected_revenue - inputs.total_booked_revenue) / inputs.total_expected_revenue * 100 if inputs.total_expected_revenue > 0 else 0.0
        values.append(self._kpi("revenue_variance", variance))

        # ── Pipeline KPIs ──
        values.append(self._kpi("pipeline_coverage", inputs.pipeline_coverage_ratio * 100))
        values.append(self._kpi("pipeline_velocity", inputs.avg_stage_velocity_days))
        values.append(self._kpi("stage_conversion", inputs.stage_conversion_rate * 100))
        values.append(self._kpi("stage_aging", inputs.stage_aging_percent * 100))

        # ── Commercial KPIs ──
        values.append(self._kpi("quote_acceptance", inputs.quote_acceptance_rate * 100))
        values.append(self._kpi("avg_discount", inputs.avg_discount_percent))
        values.append(self._kpi("approval_time", inputs.avg_approval_time_days))

        # ── Customer KPIs ──
        values.append(self._kpi("renewal_rate", inputs.contract_renewal_rate * 100))
        values.append(self._kpi("expansion_rate", inputs.contract_expansion_rate * 100))

        # ── Forecast KPIs ──
        values.append(self._kpi("forecast_accuracy", inputs.forecast_accuracy * 100))
        values.append(self._kpi("forecast_bias", inputs.forecast_bias * 100))
        values.append(self._kpi("forecast_stability", inputs.forecast_stability * 100))

        # ── Operational KPIs ──
        values.append(self._kpi("activity_sla", inputs.activity_sla_compliance * 100))
        values.append(self._kpi("rep_productivity", inputs.rep_productivity))

        snapshot = AnalyticsSnapshot(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            values=values,
        )
        result = await self._repository.save(snapshot)
        await self._emit("analytics.snapshot_generated", tenant_id, {
            "snapshot_id": snapshot.id,
            "kpi_count": len(values),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        })
        return result

    def _kpi(self, kpi_id: str, current_value: float, previous_value: float = 0.0) -> KPIValue:
        change = current_value - previous_value
        change_percent = (change / previous_value * 100) if previous_value != 0 else 0.0
        return KPIValue(
            kpi_id=kpi_id, value=current_value,
            previous_value=previous_value,
            change=round(change, 2), change_percent=round(change_percent, 2),
        )

    async def get(self, snapshot_id: str) -> AnalyticsSnapshot | None:
        return await self._repository.get(snapshot_id)

    async def get_latest(self, tenant_id: str) -> AnalyticsSnapshot | None:
        return await self._repository.get_latest(tenant_id)

    async def list_snapshots(self, tenant_id: str, limit: int = 20) -> list[AnalyticsSnapshot]:
        return await self._repository.list_by_tenant(tenant_id, limit)

    @staticmethod
    def explain(kpi_id: str) -> dict:
        """Return the formula and definition for a KPI."""
        kpi = KPIRegistry.get(kpi_id)
        if not kpi:
            return {"error": f"KPI '{kpi_id}' not found"}
        return {
            "id": kpi.id, "name": kpi.name, "name_ar": kpi.name_ar,
            "category": kpi.category.value, "formula": kpi.formula,
            "unit": kpi.unit, "source_domains": kpi.source_domains,
        }
