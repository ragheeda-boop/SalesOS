from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import (
    Territory, CoverageAnalysis, CoverageGap,
    LoadBalanceRecommendation, TerritorySummary,
)
from .repo import TerritoryRepository


class TerritoryService:
    """Manages territory CRUD, account assignment, coverage analysis, load balancing."""

    def __init__(self, repository: TerritoryRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id, aggregate_id=data.get("territory_id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def create_territory(
        self,
        tenant_id: str,
        name: str,
        region: str = "",
        rep_id: str = "",
        rep_name: str = "",
        account_ids: list[str] | None = None,
    ) -> Territory:
        territory = Territory(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            region=region,
            rep_id=rep_id,
            rep_name=rep_name,
            account_ids=list(account_ids or []),
        )
        result = await self._repository.save(territory)
        await self._emit("territory.created", tenant_id, {
            "territory_id": result.id,
            "name": name,
            "rep_id": rep_id,
            "account_count": result.account_count,
        })
        return result

    async def get_territory(self, territory_id: str) -> Territory | None:
        return await self._repository.get(territory_id)

    async def list_territories(
        self,
        tenant_id: str,
        rep_id: str | None = None,
        region: str | None = None,
        limit: int = 50,
    ) -> list[Territory]:
        return await self._repository.list_by_tenant(tenant_id, rep_id, region, limit)

    async def update_territory(
        self,
        territory_id: str,
        name: str | None = None,
        region: str | None = None,
        rep_id: str | None = None,
        rep_name: str | None = None,
    ) -> Territory:
        territory = await self._repository.get(territory_id)
        if not territory:
            raise ValueError(f"Territory {territory_id} not found")
        if name is not None:
            territory.name = name
        if region is not None:
            territory.region = region
        if rep_id is not None:
            territory.rep_id = rep_id
        if rep_name is not None:
            territory.rep_name = rep_name
        territory.updated_at = datetime.now(timezone.utc)
        return await self._repository.save(territory)

    async def delete_territory(self, territory_id: str) -> bool:
        territory = await self._repository.get(territory_id)
        if not territory:
            return False
        return await self._repository.delete(territory_id)

    async def assign_accounts(self, territory_id: str, account_ids: list[str]) -> Territory:
        territory = await self._repository.get(territory_id)
        if not territory:
            raise ValueError(f"Territory {territory_id} not found")
        existing = set(territory.account_ids)
        for aid in account_ids:
            if aid not in existing:
                territory.account_ids.append(aid)
                existing.add(aid)
        territory.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(territory)
        await self._emit("territory.accounts_assigned", territory.tenant_id, {
            "territory_id": result.id,
            "new_accounts": len(account_ids),
            "total_accounts": result.account_count,
        })
        return result

    async def unassign_accounts(self, territory_id: str, account_ids: list[str]) -> Territory:
        territory = await self._repository.get(territory_id)
        if not territory:
            raise ValueError(f"Territory {territory_id} not found")
        remove_set = set(account_ids)
        territory.account_ids = [a for a in territory.account_ids if a not in remove_set]
        territory.updated_at = datetime.now(timezone.utc)
        return await self._repository.save(territory)

    async def move_account(
        self,
        from_territory_id: str,
        to_territory_id: str,
        account_id: str,
    ) -> tuple[Territory, Territory]:
        from_t = await self._repository.get(from_territory_id)
        to_t = await self._repository.get(to_territory_id)
        if not from_t or not to_t:
            raise ValueError("Territory not found")
        if account_id in from_t.account_ids:
            from_t.account_ids = [a for a in from_t.account_ids if a != account_id]
            from_t.updated_at = datetime.now(timezone.utc)
            await self._repository.save(from_t)
        if account_id not in to_t.account_ids:
            to_t.account_ids.append(account_id)
            to_t.updated_at = datetime.now(timezone.utc)
            await self._repository.save(to_t)
        return from_t, to_t

    async def coverage_analysis(
        self,
        tenant_id: str,
        account_values: dict[str, float] | None = None,
    ) -> TerritorySummary:
        territories = await self._repository.list_by_tenant(tenant_id)
        all_account_ids: set[str] = set()
        rep_map: dict[str, dict] = {}

        for t in territories:
            for aid in t.account_ids:
                all_account_ids.add(aid)
            if t.rep_id not in rep_map:
                rep_map[t.rep_id] = {
                    "rep_id": t.rep_id,
                    "rep_name": t.rep_name,
                    "territory_count": 0,
                    "total_accounts": 0,
                    "total_pipeline_value": 0.0,
                }
            entry = rep_map[t.rep_id]
            entry["territory_count"] += 1
            entry["total_accounts"] += t.account_count
            if account_values:
                entry["total_pipeline_value"] += sum(
                    account_values.get(aid, 0.0) for aid in t.account_ids
                )

        per_rep = []
        for entry in rep_map.values():
            acct_count = entry["total_accounts"]
            per_rep.append(CoverageAnalysis(
                rep_id=entry["rep_id"],
                rep_name=entry["rep_name"],
                territory_count=entry["territory_count"],
                total_accounts=acct_count,
                total_pipeline_value=entry["total_pipeline_value"],
                accounts_per_territory=round(acct_count / entry["territory_count"], 1) if entry["territory_count"] > 0 else 0.0,
                value_per_account=round(entry["total_pipeline_value"] / acct_count, 2) if acct_count > 0 else 0.0,
            ))

        total_reps = len(rep_map)
        total_accounts = len(all_account_ids)
        avg_per_rep = round(total_accounts / total_reps, 1) if total_reps > 0 else 0.0

        return TerritorySummary(
            tenant_id=tenant_id,
            total_territories=len(territories),
            total_accounts=total_accounts,
            total_reps=total_reps,
            avg_accounts_per_rep=avg_per_rep,
            per_rep=per_rep,
        )

    async def find_gaps(
        self,
        tenant_id: str,
        known_account_ids: list[str],
        account_names: dict[str, str] | None = None,
        account_values: dict[str, float] | None = None,
    ) -> list[CoverageGap]:
        territories = await self._repository.list_by_tenant(tenant_id)
        assigned: set[str] = set()
        for t in territories:
            assigned.update(t.account_ids)
        gaps = []
        for aid in known_account_ids:
            if aid not in assigned:
                gaps.append(CoverageGap(
                    account_id=aid,
                    account_name=(account_names or {}).get(aid, ""),
                    pipeline_value=(account_values or {}).get(aid, 0.0),
                ))
        gaps.sort(key=lambda g: g.pipeline_value, reverse=True)
        return gaps

    async def load_balance(
        self,
        tenant_id: str,
        max_accounts_per_rep: int | None = None,
        account_values: dict[str, float] | None = None,
    ) -> list[LoadBalanceRecommendation]:
        territories = await self._repository.list_by_tenant(tenant_id)
        rep_accounts: dict[str, list[str]] = {}
        for t in territories:
            if t.rep_id not in rep_accounts:
                rep_accounts[t.rep_id] = []
            rep_accounts[t.rep_id].extend(t.account_ids)

        if not rep_accounts:
            return []

        if max_accounts_per_rep is None:
            total = sum(len(a) for a in rep_accounts.values())
            max_accounts_per_rep = max((total // len(rep_accounts)) + 2, 5)

        sorted_reps = sorted(rep_accounts.items(), key=lambda x: len(x[1]), reverse=True)
        overloaded = [(r, a) for r, a in sorted_reps if len(a) > max_accounts_per_rep]
        underloaded = [(r, a) for r, a in sorted_reps if len(a) < max_accounts_per_rep]

        recommendations = []
        for from_rep, from_accounts in overloaded:
            excess = len(from_accounts) - max_accounts_per_rep
            if not underloaded:
                break
            to_rep, to_accounts = underloaded[0]
            for i in range(min(excess, len(from_accounts))):
                aid = from_accounts[i]
                value = (account_values or {}).get(aid, 0.0)
                recommendations.append(LoadBalanceRecommendation(
                    account_id=aid,
                    from_rep_id=from_rep,
                    to_rep_id=to_rep,
                    reason=f"Redistribute from overloaded ({len(from_accounts)}) to underloaded ({len(to_accounts)})",
                    impact_score=round(value, 2),
                ))
                to_accounts.append(aid)
                if len(to_accounts) >= max_accounts_per_rep - 1:
                    underloaded.pop(0)
                    if not underloaded:
                        break

        return recommendations
