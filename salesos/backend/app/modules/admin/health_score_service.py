from __future__ import annotations

import uuid
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Tenant, User

from .repositories import AdminPostgresRepository


@dataclass
class HealthScoreDimension:
    name: str
    score: float
    weight: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerHealthScore:
    tenant_id: str
    tenant_name: str
    overall_score: float
    dimensions: list[HealthScoreDimension]
    trend: str
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HealthScoreRepository(AdminPostgresRepository):
    async def get_adoption_rate(self, tenant_id: str, days: int = 30) -> float:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        total_users = await self._session.execute(
            select(sa_func.count()).select_from(User).where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
        )
        total = total_users.scalar() or 0
        if total == 0:
            return 0.0
        active_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        active_users = await self._session.execute(
            select(sa_func.count()).select_from(User).where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
                User.last_login_at >= active_cutoff,
            )
        )
        active = active_users.scalar() or 0
        return round(active / total, 2)

    async def get_login_frequency(self, tenant_id: str, days: int = 30) -> float:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        total_users = await self._session.execute(
            select(sa_func.count()).select_from(User).where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
        )
        total = total_users.scalar() or 0
        if total == 0:
            return 0.0
        recent = await self._session.execute(
            select(sa_func.count()).select_from(User).where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
                User.last_login_at >= cutoff,
            )
        )
        logged_in = recent.scalar() or 0
        return round(logged_in / total, 2)

    async def get_error_rate(self, tenant_id: str, days: int = 30) -> float:
        from app.modules.audit.models import AuditLog
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        total_events = await self._session.execute(
            select(sa_func.count()).select_from(AuditLog).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.created_at >= cutoff,
            )
        )
        total = total_events.scalar() or 1
        error_events = await self._session.execute(
            select(sa_func.count()).select_from(AuditLog).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.created_at >= cutoff,
                AuditLog.action.ilike("%error%"),
            )
        )
        errors = error_events.scalar() or 0
        return round(errors / total, 4)

    async def get_support_ticket_count(self, tenant_id: str, days: int = 30) -> int:
        from app.modules.audit.models import AuditLog
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        tickets = await self._session.execute(
            select(sa_func.count()).select_from(AuditLog).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.created_at >= cutoff,
                AuditLog.action == "support_ticket_created",
            )
        )
        return tickets.scalar() or 0

    async def get_tenant_info(self, tenant_id: str) -> tuple[str, str]:
        result = await self._session.execute(
            select(Tenant.name, Tenant.plan).where(Tenant.id == tenant_id)
        )
        row = result.one_or_none()
        if row:
            return row.name, row.plan
        return "Unknown", "free"


class HealthScoreService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HealthScoreRepository(db)

    def _score_adoption(self, rate: float) -> float:
        if rate >= 0.8:
            return 1.0
        if rate >= 0.5:
            return 0.7
        if rate >= 0.3:
            return 0.4
        return 0.1

    def _score_login_frequency(self, rate: float) -> float:
        if rate >= 0.7:
            return 1.0
        if rate >= 0.4:
            return 0.6
        if rate >= 0.2:
            return 0.3
        return 0.1

    def _score_error_rate(self, rate: float) -> float:
        if rate <= 0.01:
            return 1.0
        if rate <= 0.05:
            return 0.7
        if rate <= 0.15:
            return 0.4
        return 0.1

    def _score_support_tickets(self, count: int, total_users: int) -> float:
        if total_users == 0:
            return 0.5
        per_user = count / total_users
        if per_user <= 0.1:
            return 1.0
        if per_user <= 0.3:
            return 0.7
        if per_user <= 0.5:
            return 0.4
        return 0.1

    async def calculate_health_score(self, tenant_id: str) -> CustomerHealthScore:
        adoption_rate = await self.repo.get_adoption_rate(tenant_id)
        login_freq = await self.repo.get_login_frequency(tenant_id)
        error_rate = await self.repo.get_error_rate(tenant_id)
        ticket_count = await self.repo.get_support_ticket_count(tenant_id)
        tenant_name, _ = await self.repo.get_tenant_info(tenant_id)

        total_active = await self.db.execute(
            select(sa_func.count()).select_from(User).where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
        )
        total_users = total_active.scalar() or 1

        dim_adoption = HealthScoreDimension(
            name="adoption",
            score=self._score_adoption(adoption_rate),
            weight=0.30,
            details={"adoption_rate": adoption_rate, "total_users": total_users},
        )
        dim_login = HealthScoreDimension(
            name="login_frequency",
            score=self._score_login_frequency(login_freq),
            weight=0.25,
            details={"login_rate": login_freq},
        )
        dim_error = HealthScoreDimension(
            name="error_rate",
            score=self._score_error_rate(error_rate),
            weight=0.25,
            details={"error_rate": error_rate},
        )
        dim_tickets = HealthScoreDimension(
            name="support_tickets",
            score=self._score_support_tickets(ticket_count, total_users),
            weight=0.20,
            details={"ticket_count": ticket_count, "per_user": round(ticket_count / max(total_users, 1), 2)},
        )

        dimensions = [dim_adoption, dim_login, dim_error, dim_tickets]
        overall = round(
            sum(d.score * d.weight for d in dimensions) / sum(d.weight for d in dimensions),
            2,
        )

        trend = "stable"
        if overall >= 0.8:
            trend = "healthy"
        elif overall >= 0.5:
            trend = "needs_attention"
        else:
            trend = "at_risk"

        return CustomerHealthScore(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            overall_score=overall,
            dimensions=dimensions,
            trend=trend,
        )

    async def get_all_tenant_health(self) -> list[CustomerHealthScore]:
        result = await self.db.execute(
            select(Tenant).where(Tenant.is_active.is_(True))
        )
        tenants = result.scalars().all()
        scores = []
        for tenant in tenants:
            try:
                score = await self.calculate_health_score(str(tenant.id))
                scores.append(score)
            except Exception:
                scores.append(
                    CustomerHealthScore(
                        tenant_id=str(tenant.id),
                        tenant_name=tenant.name,
                        overall_score=0.0,
                        dimensions=[],
                        trend="error",
                    )
                )
        return sorted(scores, key=lambda s: s.overall_score, reverse=True)
