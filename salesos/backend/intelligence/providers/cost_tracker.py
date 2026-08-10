"""AI Foundation F2 — Canonical persistent cost tracking with budget enforcement.

Single authoritative accounting path: LLMService only.
Individual providers MUST NOT call track() — cost is recorded once per LLM call
at the service boundary.

All cost data is PostgreSQL-backed. Budget enforcement uses SELECT FOR UPDATE
for concurrency safety. Billing periods are deterministic, month-based.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import estimate_cost
from .observability import ai_observability, format_extra

logger = logging.getLogger(__name__)


# ── Exceptions ──────────────────────────────────────────────────────

class BudgetExceededError(Exception):
    """Raised when a tenant's LLM budget is exceeded before a call is made."""
    def __init__(self, tenant_id: str, current_spend: float, budget: float):
        self.tenant_id = tenant_id
        self.current_spend = current_spend
        self.budget = budget
        super().__init__(
            f"Tenant {tenant_id} LLM budget exceeded: "
            f"${current_spend:.4f} / ${budget:.2f}"
        )


# ── Data types ──────────────────────────────────────────────────────

class BillingPeriod(str, Enum):
    MONTHLY = "monthly"


@dataclass
class BudgetConfig:
    tenant_id: str
    monthly_budget_cents: int = 0
    period_start: date | None = None
    period_spend_cents: int = 0
    is_enforced: bool = False


@dataclass
class CostRecord:
    id: str
    tenant_id: str
    provider: str
    model: str
    operation: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency_ms: float
    success: bool
    error: str | None
    retry_count: int
    timestamp: datetime
    user_id: str | None = None


@dataclass
class BudgetCheckResult:
    allowed: bool
    tenant_id: str
    monthly_budget: float
    current_spend: float
    estimated_cost: float
    would_exceed: bool


@dataclass
class PeriodSummary:
    tenant_id: str
    period_start: date
    period_end: date
    total_calls: int
    total_cost: float
    total_tokens: int
    budget_cents: int
    spend_cents: int
    is_enforced: bool


# ── CostTracker ─────────────────────────────────────────────────────

class CostTracker:
    """Canonical persistent cost tracker — exactly one per process.

    All tracking is DB-backed. Budget enforcement uses atomic
    SELECT FOR UPDATE to prevent concurrent overspend.
    """

    def __init__(self, db_session_factory: Callable[[], AsyncSession]):
        self._db_session_factory = db_session_factory

    # ── Budget management ────────────────────────────────────────

    async def set_budget(
        self,
        tenant_id: str,
        monthly_budget_cents: int,
        enforced: bool = True,
    ) -> BudgetConfig:
        async with self._db_session_factory() as session:
            period_start = date.today().replace(day=1)
            await session.execute(
                text("""
                    INSERT INTO tenant_llm_budgets
                        (tenant_id, monthly_budget_cents, period_start,
                         period_spend_cents, is_enforced)
                    VALUES
                        (:tid, :budget, :ps, 0, :enf)
                    ON CONFLICT (tenant_id) DO UPDATE SET
                        monthly_budget_cents = :budget,
                        is_enforced = :enf,
                        updated_at = now()
                """),
                {"tid": tenant_id, "budget": monthly_budget_cents,
                 "ps": period_start, "enf": enforced},
            )
            await session.commit()
        return BudgetConfig(
            tenant_id=tenant_id,
            monthly_budget_cents=monthly_budget_cents,
            period_start=period_start,
            period_spend_cents=0,
            is_enforced=enforced,
        )

    async def get_budget(self, tenant_id: str) -> BudgetConfig | None:
        async with self._db_session_factory() as session:
            row = await session.execute(
                text("""
                    SELECT tenant_id, monthly_budget_cents, period_start,
                           period_spend_cents, is_enforced
                    FROM tenant_llm_budgets
                    WHERE tenant_id = :tid
                """),
                {"tid": tenant_id},
            )
            r = row.one_or_none()
            if r is None:
                return None
            return BudgetConfig(
                tenant_id=r.tenant_id,
                monthly_budget_cents=r.monthly_budget_cents,
                period_start=r.period_start,
                period_spend_cents=r.period_spend_cents,
                is_enforced=r.is_enforced,
            )

    async def check_budget(
        self,
        tenant_id: str,
        estimated_cost: float,
    ) -> BudgetCheckResult:
        """Atomic budget check using SELECT FOR UPDATE.

        Returns BudgetCheckResult.would_exceed=True when the call would
        push the tenant over budget. Caller MUST NOT proceed when
        would_exceed is True and the budget is enforced.
        """
        async with self._db_session_factory() as session:
            async with session.begin():
                row = await session.execute(
                    text("""
                        SELECT tenant_id, monthly_budget_cents, period_start,
                               period_spend_cents, is_enforced
                        FROM tenant_llm_budgets
                        WHERE tenant_id = :tid
                        FOR UPDATE
                    """),
                    {"tid": tenant_id},
                )
                r = row.one_or_none()

                budget_cents = 0
                period_spend_cents = 0
                period_start = date.today().replace(day=1)
                is_enforced = False

                if r is not None:
                    budget_cents = r.monthly_budget_cents
                    period_spend_cents = r.period_spend_cents
                    period_start = r.period_start
                    is_enforced = r.is_enforced

                # Monthly reset: if we're in a new billing period, reset spend
                current_period = date.today().replace(day=1)
                if period_start and period_start < current_period:
                    period_spend_cents = 0
                    period_start = current_period
                    if r is not None:
                        await session.execute(
                            text("""
                                UPDATE tenant_llm_budgets
                                SET period_start = :ps,
                                    period_spend_cents = 0,
                                    updated_at = now()
                                WHERE tenant_id = :tid
                            """),
                            {"tid": tenant_id, "ps": current_period},
                        )

                monthly_budget = budget_cents / 100.0
                current_spend = period_spend_cents / 100.0
                estimated_cost_cents = int(estimated_cost * 100)
                would_exceed = (
                    is_enforced
                    and budget_cents > 0
                    and (period_spend_cents + estimated_cost_cents) > budget_cents
                )

                if would_exceed:
                    ai_observability.record_budget_rejection(tenant_id)
                    logger.warning(
                        "LLM budget exceeded",
                        extra=format_extra(
                            event="budget_exceeded",
                            tenant_id=tenant_id,
                            spend=current_spend,
                            budget=monthly_budget,
                            estimated_cost=estimated_cost,
                        ),
                    )

                return BudgetCheckResult(
                    allowed=not would_exceed,
                    tenant_id=tenant_id,
                    monthly_budget=monthly_budget,
                    current_spend=current_spend,
                    estimated_cost=estimated_cost,
                    would_exceed=would_exceed,
                )

    async def deduct_budget(self, tenant_id: str, cost: float) -> None:
        """Atomically deduct cost from tenant budget after a successful call."""
        cost_cents = int(cost * 100)
        async with self._db_session_factory() as session:
            async with session.begin():
                await session.execute(
                    text("""
                        UPDATE tenant_llm_budgets
                        SET period_spend_cents = period_spend_cents + :cost,
                            updated_at = now()
                        WHERE tenant_id = :tid
                    """),
                    {"tid": tenant_id, "cost": cost_cents},
                )

    # ── Cost recording ──────────────────────────────────────────

    async def track(
        self,
        tenant_id: str,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        operation: str = "completion",
        user_id: str | None = None,
        latency_ms: float = 0.0,
        success: bool = True,
        error: str | None = None,
        retry_count: int = 0,
    ) -> CostRecord:
        total_tokens = prompt_tokens + completion_tokens
        cost = estimate_cost(model, prompt_tokens, completion_tokens)

        record = CostRecord(
            id=uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            provider=provider,
            model=model,
            operation=operation,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=round(latency_ms, 2),
            success=success,
            error=error,
            retry_count=retry_count,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
        )

        async with self._db_session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO llm_cost_entries
                        (id, tenant_id, user_id, provider, model, operation,
                         prompt_tokens, completion_tokens, total_tokens,
                         cost, latency_ms, success, error, retry_count,
                         timestamp)
                    VALUES
                        (:id, :tenant_id, :user_id, :provider, :model,
                         :operation, :prompt_tokens, :completion_tokens,
                         :total_tokens, :cost, :latency_ms, :success,
                         :error, :retry_count, :timestamp)
                """),
                {
                    "id": record.id,
                    "tenant_id": record.tenant_id,
                    "user_id": record.user_id,
                    "provider": record.provider,
                    "model": record.model,
                    "operation": record.operation,
                    "prompt_tokens": record.prompt_tokens,
                    "completion_tokens": record.completion_tokens,
                    "total_tokens": record.total_tokens,
                    "cost": record.cost,
                    "latency_ms": record.latency_ms,
                    "success": record.success,
                    "error": record.error,
                    "retry_count": record.retry_count,
                    "timestamp": record.timestamp,
                },
            )
            await session.commit()

        return record

    # ── Queries ──────────────────────────────────────────────────

    async def get_records(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
        provider: str | None = None,
        model: str | None = None,
    ) -> list[CostRecord]:
        async with self._db_session_factory() as session:
            clauses = []
            params: dict[str, Any] = {"limit": limit}
            if tenant_id:
                clauses.append("tenant_id = :tid")
                params["tid"] = tenant_id
            if provider:
                clauses.append("provider = :prov")
                params["prov"] = provider
            if model:
                clauses.append("model = :mdl")
                params["mdl"] = model

            where = ""
            if clauses:
                where = "WHERE " + " AND ".join(clauses)

            rows = await session.execute(
                text(f"""
                    SELECT id, tenant_id, user_id, provider, model, operation,
                           prompt_tokens, completion_tokens, total_tokens,
                           cost, latency_ms, success, error, retry_count,
                           timestamp
                    FROM llm_cost_entries
                    {where}
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """),
                params,
            )
            results = []
            for r in rows.mappings().all():
                results.append(CostRecord(
                    id=r["id"],
                    tenant_id=r["tenant_id"],
                    user_id=r.get("user_id"),
                    provider=r["provider"],
                    model=r["model"],
                    operation=r["operation"],
                    prompt_tokens=r["prompt_tokens"],
                    completion_tokens=r["completion_tokens"],
                    total_tokens=r["total_tokens"],
                    cost=float(r["cost"]),
                    latency_ms=float(r["latency_ms"]),
                    success=r["success"],
                    error=r.get("error"),
                    retry_count=r["retry_count"],
                    timestamp=r["timestamp"],
                ))
            return results

    async def get_spend(
        self,
        tenant_id: str,
        since: datetime | None = None,
    ) -> float:
        async with self._db_session_factory() as session:
            if since:
                row = await session.execute(
                    text("""
                        SELECT COALESCE(SUM(cost), 0) as total
                        FROM llm_cost_entries
                        WHERE tenant_id = :tid AND success = true
                          AND timestamp >= :since
                    """),
                    {"tid": tenant_id, "since": since},
                )
            else:
                row = await session.execute(
                    text("""
                        SELECT COALESCE(SUM(cost), 0) as total
                        FROM llm_cost_entries
                        WHERE tenant_id = :tid AND success = true
                    """),
                    {"tid": tenant_id},
                )
            return float(row.scalar_one())

    async def get_period_summary(
        self,
        tenant_id: str,
    ) -> PeriodSummary:
        period_start = date.today().replace(day=1)
        period_end = date.today().replace(day=28) if date.today().month == 12 \
            else date.today().replace(month=date.today().month + 1, day=1)

        budget = await self.get_budget(tenant_id)
        spend = await self.get_spend(tenant_id)

        async with self._db_session_factory() as session:
            row = await session.execute(
                text("""
                    SELECT COUNT(*) as total_calls,
                           COALESCE(SUM(cost), 0) as total_cost,
                           COALESCE(SUM(total_tokens), 0) as total_tokens
                    FROM llm_cost_entries
                    WHERE tenant_id = :tid AND success = true
                """),
                {"tid": tenant_id},
            )
            r = row.one()
            total_calls = r.total_calls
            total_cost = float(r.total_cost)
            total_tokens = int(r.total_tokens)

        return PeriodSummary(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            total_calls=total_calls,
            total_cost=total_cost,
            total_tokens=total_tokens,
            budget_cents=budget.monthly_budget_cents if budget else 0,
            spend_cents=int(spend * 100),
            is_enforced=budget.is_enforced if budget else False,
        )


# ── Module-level singleton (lazily initialized) ────────────────────

_cost_tracker: CostTracker | None = None


def init_cost_tracker(db_session_factory: Callable[[], AsyncSession]) -> CostTracker:
    global _cost_tracker
    _cost_tracker = CostTracker(db_session_factory)
    return _cost_tracker


def get_cost_tracker() -> CostTracker:
    if _cost_tracker is None:
        raise RuntimeError(
            "CostTracker not initialized. Call init_cost_tracker(db_session_factory) first."
        )
    return _cost_tracker
