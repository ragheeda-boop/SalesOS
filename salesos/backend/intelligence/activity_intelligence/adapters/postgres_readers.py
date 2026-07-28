"""Postgres readers for Activity Intelligence — backed by synced employee events."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domains.employee.intelligence_models import (
    EmployeeCalendarEventModel,
    EmployeeEmailEventModel,
)
from intelligence.activity_intelligence.contracts.repository import (
    EmailReader,
    MeetingReader,
)


def _company_uuid(company_id: str) -> uuid.UUID:
    return uuid.UUID(company_id)


def _tenant_uuid(tenant_id: str) -> uuid.UUID:
    return uuid.UUID(tenant_id)


def _email_company_filter(company_id: uuid.UUID):
    # related_company_ids is JSONB list of UUID strings
    return EmployeeEmailEventModel.related_company_ids.contains([str(company_id)])


def _calendar_company_filter(company_id: uuid.UUID):
    return EmployeeCalendarEventModel.related_company_ids.contains([str(company_id)])


class PostgresEmailReader(EmailReader):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, email_id: str) -> Optional[dict]:
        result = await self.db.execute(
            select(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.id == uuid.UUID(email_id)
            ).limit(1)
        )
        row = result.scalar_one_or_none()
        return self._to_dict(row) if row else None

    async def list_by_company(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[dict]:
        cid = _company_uuid(company_id)
        tid = _tenant_uuid(tenant_id)
        result = await self.db.execute(
            select(EmployeeEmailEventModel)
            .where(
                EmployeeEmailEventModel.tenant_id == tid,
                _email_company_filter(cid),
            )
            .order_by(EmployeeEmailEventModel.timestamp_utc.desc())
            .limit(limit)
        )
        return [self._to_dict(r) for r in result.scalars().all()]

    async def count_by_company(
        self, company_id: str, tenant_id: str, direction: str | None = None
    ) -> int:
        cid = _company_uuid(company_id)
        tid = _tenant_uuid(tenant_id)
        clauses = [
            EmployeeEmailEventModel.tenant_id == tid,
            _email_company_filter(cid),
        ]
        if direction in ("inbound", "received"):
            clauses.append(EmployeeEmailEventModel.direction == "received")
        elif direction in ("outbound", "sent"):
            clauses.append(EmployeeEmailEventModel.direction == "sent")
        result = await self.db.scalar(
            select(func.count()).select_from(EmployeeEmailEventModel).where(and_(*clauses))
        )
        return int(result or 0)

    async def last_email(self, company_id: str, tenant_id: str) -> Optional[dict]:
        cid = _company_uuid(company_id)
        tid = _tenant_uuid(tenant_id)
        result = await self.db.execute(
            select(EmployeeEmailEventModel)
            .where(
                EmployeeEmailEventModel.tenant_id == tid,
                _email_company_filter(cid),
            )
            .order_by(EmployeeEmailEventModel.timestamp_utc.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return self._to_dict(row) if row else None

    async def tenant_totals(self, tenant_id: str) -> dict:
        tid = _tenant_uuid(tenant_id)
        total = await self.db.scalar(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.tenant_id == tid
            )
        )
        return {"email_count": int(total or 0)}

    @staticmethod
    def _to_dict(row: EmployeeEmailEventModel) -> dict:
        return {
            "id": str(row.id),
            "subject": row.subject or "",
            "from_address": row.from_address or "",
            "to_addresses": row.to_addresses or [],
            "direction": row.direction,
            "sent_at": row.timestamp_utc.isoformat() if row.timestamp_utc else None,
            "snippet": row.snippet or "",
            "company_ids": row.related_company_ids or [],
            "thread_id": row.thread_id,
        }


class PostgresMeetingReader(MeetingReader):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, meeting_id: str) -> Optional[dict]:
        result = await self.db.execute(
            select(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.id == uuid.UUID(meeting_id)
            ).limit(1)
        )
        row = result.scalar_one_or_none()
        return self._to_dict(row) if row else None

    async def list_by_company(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[dict]:
        cid = _company_uuid(company_id)
        tid = _tenant_uuid(tenant_id)
        result = await self.db.execute(
            select(EmployeeCalendarEventModel)
            .where(
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,  # noqa: E712
                _calendar_company_filter(cid),
            )
            .order_by(EmployeeCalendarEventModel.start_utc.desc())
            .limit(limit)
        )
        return [self._to_dict(r) for r in result.scalars().all()]

    async def count_by_company(self, company_id: str, tenant_id: str) -> int:
        cid = _company_uuid(company_id)
        tid = _tenant_uuid(tenant_id)
        result = await self.db.scalar(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,  # noqa: E712
                _calendar_company_filter(cid),
            )
        )
        return int(result or 0)

    async def last_meeting(self, company_id: str, tenant_id: str) -> Optional[dict]:
        cid = _company_uuid(company_id)
        tid = _tenant_uuid(tenant_id)
        result = await self.db.execute(
            select(EmployeeCalendarEventModel)
            .where(
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,  # noqa: E712
                _calendar_company_filter(cid),
            )
            .order_by(EmployeeCalendarEventModel.start_utc.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return self._to_dict(row) if row else None

    async def tenant_totals(self, tenant_id: str) -> dict:
        tid = _tenant_uuid(tenant_id)
        total = await self.db.scalar(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,  # noqa: E712
            )
        )
        return {"meeting_count": int(total or 0)}

    @staticmethod
    def _to_dict(row: EmployeeCalendarEventModel) -> dict:
        duration = row.duration_minutes or 0
        if not duration and row.start_utc and row.end_utc:
            duration = int((row.end_utc - row.start_utc).total_seconds() / 60)
        return {
            "id": str(row.id),
            "title": row.title or "",
            "date": row.start_utc.isoformat() if row.start_utc else None,
            "duration_minutes": duration,
            "status": "cancelled" if row.is_cancelled else "completed",
            "attendees_count": row.attendees_count or 0,
            "company_ids": row.related_company_ids or [],
            "is_internal": bool(row.is_internal),
        }
