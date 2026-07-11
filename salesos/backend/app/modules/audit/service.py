from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

from .models import AuditLog


class AuditRepository(ABC):
    @abstractmethod
    async def create(self, entry: AuditLog) -> AuditLog: ...

    @abstractmethod
    async def query(
        self,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[AuditLog], int]: ...

    @abstractmethod
    async def stats(
        self,
        tenant_id: str,
        days: int = 30,
    ) -> dict[str, Any]: ...


class PostgresAuditRepository(AuditRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entry: AuditLog) -> AuditLog:
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def query(
        self,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        count_query = select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id == tenant_id)

        if filters:
            conditions = []
            if "action" in filters:
                conditions.append(AuditLog.action == filters["action"])
            if "resource_type" in filters:
                conditions.append(AuditLog.resource_type == filters["resource_type"])
            if "user_id" in filters:
                conditions.append(AuditLog.user_id == filters["user_id"])
            if "resource_id" in filters:
                conditions.append(AuditLog.resource_id == filters["resource_id"])
            if "date_from" in filters:
                conditions.append(AuditLog.created_at >= filters["date_from"])
            if "date_to" in filters:
                conditions.append(AuditLog.created_at <= filters["date_to"])
            if "search" in filters:
                conditions.append(AuditLog.details.cast(func.text()).ilike(f"%{filters['search']}%"))

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(AuditLog.created_at))
        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        entries = list(result.scalars().all())
        return entries, total

    async def stats(self, tenant_id: str, days: int = 30) -> dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        base = select(AuditLog).where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at >= since,
        )

        total_result = await self.db.execute(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.created_at >= since,
            )
        )
        total_events = total_result.scalar() or 0

        top_users_result = await self.db.execute(
            select(AuditLog.user_id, func.count().label("cnt"))
            .where(AuditLog.tenant_id == tenant_id, AuditLog.created_at >= since, AuditLog.user_id.isnot(None))
            .group_by(AuditLog.user_id)
            .order_by(desc("cnt"))
            .limit(10)
        )
        top_users = [{"user_id": row[0], "count": row[1]} for row in top_users_result]

        top_actions_result = await self.db.execute(
            select(AuditLog.action, func.count().label("cnt"))
            .where(AuditLog.tenant_id == tenant_id, AuditLog.created_at >= since)
            .group_by(AuditLog.action)
            .order_by(desc("cnt"))
            .limit(10)
        )
        top_actions = [{"action": row[0], "count": row[1]} for row in top_actions_result]

        resource_breakdown_result = await self.db.execute(
            select(AuditLog.resource_type, func.count().label("cnt"))
            .where(AuditLog.tenant_id == tenant_id, AuditLog.created_at >= since)
            .group_by(AuditLog.resource_type)
            .order_by(desc("cnt"))
            .limit(20)
        )
        resource_breakdown = [{"resource_type": row[0], "count": row[1]} for row in resource_breakdown_result]

        return {
            "total_events": total_events,
            "period_days": days,
            "top_users": top_users,
            "top_actions": top_actions,
            "resource_breakdown": resource_breakdown,
        }


class InMemoryAuditRepository(AuditRepository):
    def __init__(self):
        self._entries: list[AuditLog] = []
        self._counter = 0

    async def create(self, entry: AuditLog) -> AuditLog:
        self._counter += 1
        entry.id = self._counter
        if entry.created_at is None:
            entry.created_at = datetime.now(timezone.utc)
        self._entries.append(entry)
        return entry

    async def query(
        self,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        filtered = [e for e in self._entries if e.tenant_id == tenant_id]
        if filters:
            if "action" in filters:
                filtered = [e for e in filtered if e.action == filters["action"]]
            if "resource_type" in filters:
                filtered = [e for e in filtered if e.resource_type == filters["resource_type"]]
            if "user_id" in filters:
                filtered = [e for e in filtered if e.user_id == filters["user_id"]]
            if "resource_id" in filters:
                filtered = [e for e in filtered if e.resource_id == filters["resource_id"]]
            if "date_from" in filters:
                filtered = [e for e in filtered if e.created_at and e.created_at >= filters["date_from"]]
            if "date_to" in filters:
                filtered = [e for e in filtered if e.created_at and e.created_at <= filters["date_to"]]

        filtered.sort(key=lambda e: e.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        total = len(filtered)
        start = (page - 1) * size
        end = start + size
        return filtered[start:end], total

    async def stats(self, tenant_id: str, days: int = 30) -> dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = [e for e in self._entries if e.tenant_id == tenant_id and e.created_at and e.created_at >= since]

        total_events = len(filtered)
        user_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        resource_counts: dict[str, int] = {}

        for e in filtered:
            if e.user_id:
                user_counts[e.user_id] = user_counts.get(e.user_id, 0) + 1
            action_counts[e.action] = action_counts.get(e.action, 0) + 1
            resource_counts[e.resource_type] = resource_counts.get(e.resource_type, 0) + 1

        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        resource_breakdown = sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            "total_events": total_events,
            "period_days": days,
            "top_users": [{"user_id": u, "count": c} for u, c in top_users],
            "top_actions": [{"action": a, "count": c} for a, c in top_actions],
            "resource_breakdown": [{"resource_type": r, "count": c} for r, c in resource_breakdown],
        }


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    async def log(
        self,
        tenant_id: str,
        user_id: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            tenant_id=tenant_id or "",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        return await self.repository.create(entry)

    async def query(
        self,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        return await self.repository.query(tenant_id, filters, page, size)

    async def stats(self, tenant_id: str, days: int = 30) -> dict[str, Any]:
        return await self.repository.stats(tenant_id, days)
