"""Postgres readers for Activity Intelligence engines (ADR-012).

Reads from employee_email_events / employee_calendar_events populated by
Communication Hub Google sync. Company linkage uses related_company_ids.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from intelligence.activity_intelligence.contracts.repository import EmailReader, MeetingReader


class PostgresEmailReader(EmailReader):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, email_id: str) -> Optional[dict]:
        row = (
            await self.db.execute(
                sa_text("""
                    SELECT id::text, subject, direction, from_address, timestamp_utc AS sent_at
                    FROM employee_email_events
                    WHERE id = :id
                    LIMIT 1
                """),
                {"id": email_id},
            )
        ).mappings().first()
        return dict(row) if row else None

    async def list_by_company(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[dict]:
        rows = (
            await self.db.execute(
                sa_text("""
                    SELECT id::text, subject, direction, from_address, timestamp_utc AS sent_at
                    FROM employee_email_events
                    WHERE tenant_id = :tid
                      AND related_company_ids @> to_jsonb(:company_id::text)
                    ORDER BY timestamp_utc DESC
                    LIMIT :lim
                """),
                {"tid": tenant_id, "company_id": company_id, "lim": limit},
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    async def count_by_company(
        self, company_id: str, tenant_id: str, direction: str | None = None
    ) -> int:
        conditions = """
            tenant_id = :tid
            AND related_company_ids @> to_jsonb(:company_id::text)
        """
        params: dict = {"tid": tenant_id, "company_id": company_id}
        if direction:
            conditions += " AND direction = :direction"
            params["direction"] = direction
        row = (
            await self.db.execute(
                sa_text(f"SELECT COUNT(*) AS c FROM employee_email_events WHERE {conditions}"),
                params,
            )
        ).mappings().one()
        return int(row["c"] or 0)

    async def last_email(self, company_id: str, tenant_id: str) -> Optional[dict]:
        row = (
            await self.db.execute(
                sa_text("""
                    SELECT id::text, subject, direction, from_address, timestamp_utc AS sent_at
                    FROM employee_email_events
                    WHERE tenant_id = :tid
                      AND related_company_ids @> to_jsonb(:company_id::text)
                    ORDER BY timestamp_utc DESC
                    LIMIT 1
                """),
                {"tid": tenant_id, "company_id": company_id},
            )
        ).mappings().first()
        return dict(row) if row else None

    async def count_by_employee(
        self, employee_id: str, tenant_id: str, direction: str | None = None
    ) -> int:
        conditions = "tenant_id = :tid AND employee_id = :eid"
        params: dict = {"tid": tenant_id, "eid": employee_id}
        if direction:
            conditions += " AND direction = :direction"
            params["direction"] = direction
        row = (
            await self.db.execute(
                sa_text(f"SELECT COUNT(*) AS c FROM employee_email_events WHERE {conditions}"),
                params,
            )
        ).mappings().one()
        return int(row["c"] or 0)


class PostgresMeetingReader(MeetingReader):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, meeting_id: str) -> Optional[dict]:
        row = (
            await self.db.execute(
                sa_text("""
                    SELECT id::text, title, start_utc AS date, duration_minutes,
                           CASE WHEN is_cancelled THEN 'cancelled' ELSE 'completed' END AS status
                    FROM employee_calendar_events
                    WHERE id = :id
                    LIMIT 1
                """),
                {"id": meeting_id},
            )
        ).mappings().first()
        return dict(row) if row else None

    async def list_by_company(
        self, company_id: str, tenant_id: str, limit: int = 50
    ) -> list[dict]:
        rows = (
            await self.db.execute(
                sa_text("""
                    SELECT id::text, title, start_utc AS date, duration_minutes,
                           CASE WHEN is_cancelled THEN 'cancelled' ELSE 'completed' END AS status
                    FROM employee_calendar_events
                    WHERE tenant_id = :tid
                      AND related_company_ids @> to_jsonb(:company_id::text)
                    ORDER BY start_utc DESC
                    LIMIT :lim
                """),
                {"tid": tenant_id, "company_id": company_id, "lim": limit},
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    async def count_by_company(self, company_id: str, tenant_id: str) -> int:
        row = (
            await self.db.execute(
                sa_text("""
                    SELECT COUNT(*) AS c
                    FROM employee_calendar_events
                    WHERE tenant_id = :tid
                      AND related_company_ids @> to_jsonb(:company_id::text)
                      AND is_cancelled = false
                """),
                {"tid": tenant_id, "company_id": company_id},
            )
        ).mappings().one()
        return int(row["c"] or 0)

    async def last_meeting(self, company_id: str, tenant_id: str) -> Optional[dict]:
        row = (
            await self.db.execute(
                sa_text("""
                    SELECT id::text, title, start_utc AS date, duration_minutes,
                           CASE WHEN is_cancelled THEN 'cancelled' ELSE 'completed' END AS status
                    FROM employee_calendar_events
                    WHERE tenant_id = :tid
                      AND related_company_ids @> to_jsonb(:company_id::text)
                    ORDER BY start_utc DESC
                    LIMIT 1
                """),
                {"tid": tenant_id, "company_id": company_id},
            )
        ).mappings().first()
        return dict(row) if row else None

    async def count_by_employee(self, employee_id: str, tenant_id: str) -> int:
        row = (
            await self.db.execute(
                sa_text("""
                    SELECT COUNT(*) AS c
                    FROM employee_calendar_events
                    WHERE tenant_id = :tid AND employee_id = :eid AND is_cancelled = false
                """),
                {"tid": tenant_id, "eid": employee_id},
            )
        ).mappings().one()
        return int(row["c"] or 0)

    async def hours_by_employee(self, employee_id: str, tenant_id: str) -> float:
        row = (
            await self.db.execute(
                sa_text("""
                    SELECT COALESCE(SUM(duration_minutes), 0) AS minutes
                    FROM employee_calendar_events
                    WHERE tenant_id = :tid AND employee_id = :eid AND is_cancelled = false
                """),
                {"tid": tenant_id, "eid": employee_id},
            )
        ).mappings().one()
        return round(float(row["minutes"] or 0) / 60.0, 1)


def build_company_engines(db: AsyncSession):
    """Factory used by Company 360 ADR-012 block."""
    from intelligence.activity_intelligence.engine.calendar_engine import CalendarEngine
    from intelligence.activity_intelligence.engine.email_engine import EmailEngine
    from intelligence.activity_intelligence.engine.engagement_engine import EngagementEngine
    from intelligence.activity_intelligence.engine.followup_engine import FollowupEngine

    email_reader = PostgresEmailReader(db)
    meeting_reader = PostgresMeetingReader(db)
    email_eng = EmailEngine(email_reader=email_reader)
    calendar_eng = CalendarEngine(meeting_reader=meeting_reader)
    engagement_eng = EngagementEngine(email_engine=email_eng, calendar_engine=calendar_eng)
    followup_eng = FollowupEngine(email_engine=email_eng, calendar_engine=calendar_eng)
    return email_eng, calendar_eng, engagement_eng, followup_eng
