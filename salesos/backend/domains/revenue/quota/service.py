from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import (
    Quota, QuotaPeriod, QuotaStatus,
    QuotaForecast, QuotaSnapshot, TeamAggregate,
)
from .repo import QuotaRepository


class QuotaService:
    """Manages quota CRUD, attainment tracking, and forecast attainment."""

    def __init__(self, repository: QuotaRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id, aggregate_id=data.get("quota_id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def create_quota(
        self,
        tenant_id: str,
        rep_id: str,
        target_amount: float,
        period: QuotaPeriod = QuotaPeriod.QUARTERLY,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        rep_name: str = "",
    ) -> Quota:
        now = datetime.now(timezone.utc)
        if start_date is None:
            start_date = now
        if end_date is None:
            end_date = _default_end_date(period, now)

        quota = Quota(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            rep_id=rep_id,
            rep_name=rep_name,
            period=period,
            target_amount=target_amount,
            attained_amount=0.0,
            start_date=start_date,
            end_date=end_date,
            status=QuotaStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        result = await self._repository.save(quota)
        await self._emit("quota.created", tenant_id, {
            "quota_id": result.id,
            "rep_id": rep_id,
            "target_amount": target_amount,
            "period": period.value,
        })
        return result

    async def get_quota(self, quota_id: str) -> Quota | None:
        return await self._repository.get(quota_id)

    async def list_quotas(
        self,
        tenant_id: str,
        rep_id: str | None = None,
        period: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Quota]:
        return await self._repository.list_by_tenant(tenant_id, rep_id, period, status, limit)

    async def update_attainment(self, quota_id: str, attained_amount: float) -> Quota:
        quota = await self._repository.get(quota_id)
        if not quota:
            raise ValueError(f"Quota {quota_id} not found")
        quota.attained_amount = attained_amount
        quota.updated_at = datetime.now(timezone.utc)
        if quota.attained_amount >= quota.target_amount:
            quota.status = QuotaStatus.COMPLETED
        result = await self._repository.save(quota)
        await self._emit("quota.attainment_updated", quota.tenant_id, {
            "quota_id": result.id,
            "rep_id": result.rep_id,
            "attained": attained_amount,
            "target": result.target_amount,
            "attainment_percent": result.attainment_percent,
        })
        return result

    async def increment_attainment(self, quota_id: str, additional: float) -> Quota:
        quota = await self._repository.get(quota_id)
        if not quota:
            raise ValueError(f"Quota {quota_id} not found")
        return await self.update_attainment(quota_id, quota.attained_amount + additional)

    async def forecast_attainment(
        self,
        tenant_id: str,
        rep_id: str,
        closed_revenue: float,
        period_days_elapsed: float,
        total_period_days: float,
    ) -> QuotaForecast:
        quota = await self._repository.get_active_quota(tenant_id, rep_id)
        if not quota:
            return QuotaForecast(quota_id="", rep_id=rep_id)

        days_remaining = max(total_period_days - period_days_elapsed, 0.0)
        velocity = closed_revenue / period_days_elapsed if period_days_elapsed > 0 else 0.0
        projected = closed_revenue + (velocity * days_remaining)

        attainment_pct = 0.0
        if quota.target_amount > 0:
            attainment_pct = round((projected / quota.target_amount) * 100, 2)

        velocity_confidence = min(period_days_elapsed / total_period_days, 1.0)

        return QuotaForecast(
            quota_id=quota.id,
            rep_id=rep_id,
            current_velocity=round(velocity, 2),
            days_remaining=round(days_remaining, 1),
            projected_attainment=round(projected, 2),
            projected_attainment_percent=attainment_pct,
            will_hit_target=projected >= quota.target_amount,
            confidence=round(velocity_confidence, 2),
        )

    async def get_per_rep_view(self, tenant_id: str) -> list[dict]:
        quotas = await self._repository.list_by_tenant(tenant_id)
        view = {}
        for q in quotas:
            if q.rep_id not in view:
                view[q.rep_id] = {
                    "rep_id": q.rep_id,
                    "rep_name": q.rep_name,
                    "total_target": 0.0,
                    "total_attained": 0.0,
                    "quotas": 0,
                }
            entry = view[q.rep_id]
            entry["total_target"] += q.target_amount
            entry["total_attained"] += q.attained_amount
            entry["quotas"] += 1

        result = []
        for rep_data in view.values():
            pct = 0.0
            if rep_data["total_target"] > 0:
                pct = round((rep_data["total_attained"] / rep_data["total_target"]) * 100, 2)
            rep_data["attainment_percent"] = pct
            result.append(rep_data)
        return result

    async def get_team_aggregate(self, tenant_id: str) -> TeamAggregate:
        quotas = await self._repository.list_by_tenant(tenant_id)
        total_target = sum(q.target_amount for q in quotas)
        total_attained = sum(q.attained_amount for q in quotas)
        rep_ids = set()
        on_track = 0
        at_risk = 0
        missed = 0
        for q in quotas:
            rep_ids.add(q.rep_id)
            pct = q.attainment_percent
            if pct >= 100:
                on_track += 1
            elif pct >= 70:
                at_risk += 1
            else:
                missed += 1
        overall_pct = round((total_attained / total_target) * 100, 2) if total_target > 0 else 0.0
        return TeamAggregate(
            tenant_id=tenant_id,
            total_targets=total_target,
            total_attained=total_attained,
            overall_attainment_percent=overall_pct,
            rep_count=len(rep_ids),
            reps_on_track=on_track,
            reps_at_risk=at_risk,
            reps_missed=missed,
        )

    async def take_snapshot(self, tenant_id: str, period_label: str = "") -> QuotaSnapshot:
        quotas = await self._repository.list_by_tenant(tenant_id)
        team = await self.get_team_aggregate(tenant_id)
        snapshot = QuotaSnapshot(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            period_label=period_label or datetime.now(timezone.utc).strftime("%Y-Q%q"),
            quotas=quotas,
            team=team,
        )
        return await self._repository.save_snapshot(snapshot)

    async def delete_quota(self, quota_id: str) -> bool:
        return await self._repository.delete(quota_id)

    async def list_snapshots(self, tenant_id: str, limit: int = 10) -> list[QuotaSnapshot]:
        return await self._repository.list_snapshots(tenant_id, limit)


def _default_end_date(period: QuotaPeriod, start: datetime) -> datetime:
    from datetime import timedelta
    if period == QuotaPeriod.MONTHLY:
        return start + timedelta(days=30)
    if period == QuotaPeriod.QUARTERLY:
        return start + timedelta(days=91)
    return start + timedelta(days=365)
