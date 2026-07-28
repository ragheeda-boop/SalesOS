"""Email Intelligence service — KPI computation from employee_email_events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .intelligence_models import EmployeeEmailEventModel


class EmailIntelligenceService:
    """Computes email KPIs from synced employee email events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_kpis(self, employee_id: str, tenant_id: str, days: int = 30) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=days)
        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)

        sent_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.direction.in_(("sent", "outbound")),
            )
        )).scalar() or 0

        received_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.direction.in_(("received", "inbound")),
            )
        )).scalar() or 0

        internal_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.is_internal == True,
            )
        )).scalar() or 0

        total = sent_count + received_count
        external_count = max(0, total - internal_count)

        avg_response = (await self.db.execute(
            select(func.avg(EmployeeEmailEventModel.response_time_seconds)).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.response_time_seconds.isnot(None),
            )
        )).scalar()

        avg_response_hours = round((avg_response or 0) / 3600.0, 2) if avg_response else 0.0

        unread = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.is_read == False,
            )
        )).scalar() or 0

        positive_sentiment = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.ai_sentiment == "positive",
            )
        )).scalar() or 0

        negative_sentiment = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.ai_sentiment == "negative",
            )
        )).scalar() or 0

        with_attachments = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.has_attachments == True,
            )
        )).scalar() or 0

        return {
            "sent": sent_count,
            "received": received_count,
            "total": total,
            "internal": internal_count,
            "external": external_count,
            "reply_rate": round(sent_count / max(1, received_count) * 100, 1),
            "avg_response_hours": avg_response_hours,
            "unread_count": unread,
            "has_attachments": with_attachments,
            "sentiment_positive": positive_sentiment,
            "sentiment_negative": negative_sentiment,
            "period_days": days,
        }

    async def get_top_contacts(self, employee_id: str, tenant_id: str, limit: int = 10) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=90)
        result = await self.db.execute(
            select(
                EmployeeEmailEventModel.from_address,
                func.count().label("cnt"),
            ).where(
                EmployeeEmailEventModel.employee_id == uuid.UUID(employee_id),
                EmployeeEmailEventModel.tenant_id == uuid.UUID(tenant_id),
                EmployeeEmailEventModel.timestamp_utc >= since,
                EmployeeEmailEventModel.is_internal == False,
            ).group_by(EmployeeEmailEventModel.from_address).order_by(desc("cnt")).limit(limit)
        )
        return [{"address": row[0], "count": row[1]} for row in result.fetchall()]

    async def get_daily_volume(self, employee_id: str, tenant_id: str, days: int = 30) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(
                func.date_trunc("day", EmployeeEmailEventModel.timestamp_utc).label("day"),
                EmployeeEmailEventModel.direction,
                func.count().label("cnt"),
            ).where(
                EmployeeEmailEventModel.employee_id == uuid.UUID(employee_id),
                EmployeeEmailEventModel.tenant_id == uuid.UUID(tenant_id),
                EmployeeEmailEventModel.timestamp_utc >= since,
            ).group_by("day", EmployeeEmailEventModel.direction).order_by("day")
        )
        daily: dict[str, dict] = {}
        for row in result.fetchall():
            day_str = str(row[0])
            daily.setdefault(day_str, {"date": day_str, "sent": 0, "received": 0})
            if row[1] in ("sent", "outbound"):
                daily[day_str]["sent"] = row[2]
            else:
                daily[day_str]["received"] = row[2]
        return list(daily.values())
