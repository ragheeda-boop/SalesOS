from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from sdk.config import sdk_settings

from .base import MODEL_COST_PER_1K_TOKENS, DEFAULT_COST, estimate_cost

MODEL_COST_PER_1K_TOKENS.update({
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.00025, "output": 0.00125},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
})


@dataclass
class CostRecord:
    id: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency_ms: float
    operation: str
    tenant_id: str | None = None
    user_id: str | None = None
    success: bool = True
    error: str | None = None
    retry_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BudgetEnforcement:
    tenant_id: str
    monthly_budget: float
    current_spend: float = 0.0
    is_exceeded: bool = False


class CostTracker:
    def __init__(self, db_session_factory=None):
        self._db_session_factory = db_session_factory
        self._budgets: dict[str, BudgetEnforcement] = {}
        self._records: list[CostRecord] = []

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        return estimate_cost(model, prompt_tokens, completion_tokens)

    def track(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        operation: str = "completion",
        tenant_id: str | None = None,
        user_id: str | None = None,
        latency_ms: float = 0.0,
        success: bool = True,
        error: str | None = None,
        retry_count: int = 0,
        persist: bool = False,
    ) -> CostRecord:
        total_tokens = prompt_tokens + completion_tokens
        cost = self.estimate_cost(model, prompt_tokens, completion_tokens)

        record = CostRecord(
            id=uuid.uuid4().hex[:12],
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=round(latency_ms, 2),
            operation=operation,
            tenant_id=tenant_id,
            user_id=user_id,
            success=success,
            error=error,
            retry_count=retry_count,
        )
        self._records.append(record)

        if persist and self._db_session_factory:
            self._persist_to_db(record)

        if tenant_id:
            self._check_budget(tenant_id, cost)

        return record

    def track_usage(self, model: str, usage: dict[str, int], operation: str = "completion", tenant_id: str | None = None) -> CostRecord:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return self.track(
            provider="unknown",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            operation=operation,
            tenant_id=tenant_id,
        )

    def set_budget(self, tenant_id: str, monthly_budget: float):
        current = self._budgets.get(tenant_id)
        if current:
            current.monthly_budget = monthly_budget
        else:
            self._budgets[tenant_id] = BudgetEnforcement(
                tenant_id=tenant_id,
                monthly_budget=monthly_budget,
            )

    def get_spend(self, tenant_id: str) -> float:
        return sum(r.cost for r in self._records if r.tenant_id == tenant_id)

    def get_records(self, limit: int = 100, tenant_id: str | None = None) -> list[CostRecord]:
        records = self._records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        return sorted(records, key=lambda r: r.timestamp, reverse=True)[:limit]

    def is_budget_exceeded(self, tenant_id: str) -> bool:
        budget = self._budgets.get(tenant_id)
        if not budget:
            return False
        budget.current_spend = self.get_spend(tenant_id)
        if budget.current_spend > budget.monthly_budget:
            budget.is_exceeded = True
        return budget.is_exceeded

    def _check_budget(self, tenant_id: str, cost: float):
        budget = self._budgets.get(tenant_id)
        if budget:
            budget.current_spend += cost
            if budget.current_spend > budget.monthly_budget:
                budget.is_exceeded = True

    async def persist_to_db(self, record: CostRecord | None = None) -> None:
        if not self._db_session_factory:
            return
        records = [record] if record else self._records
        async with self._db_session_factory() as session:
            for r in records:
                await session.execute(
                    text("""
                        INSERT INTO llm_cost_tracking
                            (id, provider, model, prompt_tokens, completion_tokens, total_tokens, cost, latency_ms, operation, tenant_id, user_id, success, error, retry_count, timestamp)
                        VALUES
                            (:id, :provider, :model, :prompt_tokens, :completion_tokens, :total_tokens, :cost, :latency_ms, :operation, :tenant_id, :user_id, :success, :error, :retry_count, :timestamp)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": r.id,
                        "provider": r.provider,
                        "model": r.model,
                        "prompt_tokens": r.prompt_tokens,
                        "completion_tokens": r.completion_tokens,
                        "total_tokens": r.total_tokens,
                        "cost": r.cost,
                        "latency_ms": r.latency_ms,
                        "operation": r.operation,
                        "tenant_id": r.tenant_id,
                        "user_id": r.user_id,
                        "success": r.success,
                        "error": r.error,
                        "retry_count": r.retry_count,
                        "timestamp": r.timestamp,
                    },
                )
            await session.commit()

    async def load_records_from_db(self, tenant_id: str | None = None, limit: int = 100) -> list[CostRecord]:
        if not self._db_session_factory:
            return []
        async with self._db_session_factory() as session:
            if tenant_id:
                rows = await session.execute(
                    text("SELECT * FROM llm_cost_tracking WHERE tenant_id = :tenant_id ORDER BY timestamp DESC LIMIT :limit"),
                    {"tenant_id": tenant_id, "limit": limit},
                )
            else:
                rows = await session.execute(
                    text("SELECT * FROM llm_cost_tracking ORDER BY timestamp DESC LIMIT :limit"),
                    {"limit": limit},
                )
            results = []
            for row in rows.mappings().all():
                d = dict(row)
                results.append(CostRecord(
                    id=d["id"],
                    provider=d["provider"],
                    model=d["model"],
                    prompt_tokens=d["prompt_tokens"],
                    completion_tokens=d["completion_tokens"],
                    total_tokens=d["total_tokens"],
                    cost=float(d["cost"]),
                    latency_ms=float(d["latency_ms"]),
                    operation=d["operation"],
                    tenant_id=d.get("tenant_id"),
                    user_id=d.get("user_id"),
                    success=d.get("success", True),
                    error=d.get("error"),
                    retry_count=d.get("retry_count", 0),
                    timestamp=d["timestamp"],
                ))
            return results

    def get_summary(self, tenant_id: str | None = None) -> dict[str, Any]:
        records = self._records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]

        if not records:
            return {"total_calls": 0, "total_cost": 0.0}

        total_cost = sum(r.cost for r in records)
        total_tokens = sum(r.total_tokens for r in records)
        total_latency = sum(r.latency_ms for r in records)
        failed = sum(1 for r in records if not r.success)

        return {
            "total_calls": len(records),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "avg_cost_per_call": round(total_cost / len(records), 6),
            "avg_latency_ms": round(total_latency / len(records), 2),
            "failed_calls": failed,
            "success_rate": round((len(records) - failed) / len(records) * 100, 1),
            "by_provider": self._group_by(records, "provider"),
            "by_model": self._group_by(records, "model"),
        }

    def _group_by(self, records: list[CostRecord], key: str) -> dict[str, dict[str, Any]]:
        groups: dict[str, list[CostRecord]] = {}
        for r in records:
            val = getattr(r, key, "unknown")
            groups.setdefault(val, []).append(r)

        result = {}
        for val, group in groups.items():
            result[val] = {
                "calls": len(group),
                "total_cost": round(sum(r.cost for r in group), 4),
                "total_tokens": sum(r.total_tokens for r in group),
            }
        return result


_cost_tracker = CostTracker()


def get_cost_tracker() -> CostTracker:
    return _cost_tracker
