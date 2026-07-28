"""Google Calendar Sync Service — orchestrates calendar event synchronization.

Flow:
  1. Fetch valid token from GoogleAccount (refresh if needed)
  2. Call Calendar API (incremental via syncToken when available, else time-range)
  3. Upsert into employee_calendar_events table
  4. Persist nextSyncToken + update GoogleAccount.last_sync_at
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication_hub.company_linker import resolve_company_ids_for_addresses
from app.modules.communication_hub.models import GoogleAccount
from app.modules.communication_hub.repository import GoogleAccountRepository
from app.modules.communication_hub.service import GoogleOAuthService
from intelligence.activity_intelligence.providers.google.calendar_provider import (
    GoogleCalendarProvider,
    CalendarAPIError,
)
from intelligence.activity_intelligence.contracts.models import RawCalendarEvent

logger = logging.getLogger(__name__)


class CalendarSyncError(Exception):
    pass


class CalendarSyncService:
    """Orchestrates Google Calendar sync for a connected account."""

    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = GoogleAccountRepository(db)
        self._oauth = GoogleOAuthService(db, tenant_id, user_id)
        self._provider: GoogleCalendarProvider | None = None

    async def _ensure_provider(self, account: GoogleAccount) -> GoogleCalendarProvider:
        token = await self._oauth.get_valid_token(account)
        provider = GoogleCalendarProvider(access_token=token, email=account.email)
        self._provider = provider
        return provider

    async def sync(self, days_lookback: int = 90, days_forward: int = 90) -> dict:
        account = await self.repo.get_by_user(self.tenant_id, self.user_id)
        if not account:
            raise CalendarSyncError("No active Google account connected")

        provider = await self._ensure_provider(account)

        try:
            events, next_sync_token = await self._fetch_events(
                account, provider, days_lookback, days_forward
            )
            result = await self._process_events(account, events)

            if next_sync_token:
                await self.repo.update_calendar_sync_token(
                    account.id, next_sync_token, tenant_id=self.tenant_id
                )
            await self.repo.update_last_sync(account.id, tenant_id=self.tenant_id)
            await self.db.commit()

            return {**result, "next_sync_token": next_sync_token}
        except CalendarAPIError as e:
            if e.status in (401, 403):
                raise CalendarSyncError(f"Calendar API authentication failed: {e}") from e
            raise CalendarSyncError(f"Calendar API error: {e}") from e
        finally:
            await provider.close()

    async def _fetch_events(
        self,
        account: GoogleAccount,
        provider: GoogleCalendarProvider,
        days_lookback: int,
        days_forward: int,
    ) -> tuple[list[RawCalendarEvent], str | None]:
        sync_token = account.calendar_sync_token
        if sync_token:
            try:
                return await provider.fetch_events(sync_token=sync_token)
            except CalendarAPIError as e:
                if e.status != 410:
                    raise
                logger.warning(
                    "calendar.sync_token.stale",
                    extra={"account_id": str(account.id)},
                )
                await self.repo.update_calendar_sync_token(
                    account.id, None, tenant_id=self.tenant_id
                )

        since = datetime.now(timezone.utc) - timedelta(days=days_lookback)
        until = datetime.now(timezone.utc) + timedelta(days=days_forward)
        return await provider.fetch_events_time_range(since=since, until=until)

    async def _process_events(self, account: GoogleAccount, events: list[RawCalendarEvent]) -> dict:
        new_count = 0
        updated_count = 0
        cancelled_count = 0
        errors: list[str] = []

        for raw in events:
            try:
                is_cancelled = raw.status == "cancelled"
                existing = await self._get_existing_event(raw.event_id)

                if existing:
                    if is_cancelled:
                        await self._mark_cancelled(existing["id"])
                        cancelled_count += 1
                    else:
                        await self._update_event(existing["id"], raw)
                        updated_count += 1
                elif not is_cancelled:
                    await self._insert_event(account, raw)
                    new_count += 1
            except Exception as e:
                errors.append(f"Event {raw.event_id}: {e}")
                logger.exception(
                    "calendar_sync.event.failed",
                    extra={"event_id": raw.event_id, "error": str(e)},
                )

        return {
            "synced_count": len(events),
            "new_count": new_count,
            "updated_count": updated_count,
            "cancelled_count": cancelled_count,
            "errors": errors,
        }

    async def _insert_event(self, account: GoogleAccount, raw: RawCalendarEvent) -> None:
        start_utc = raw.start_time or datetime.now(timezone.utc)
        end_utc = raw.end_time or datetime.now(timezone.utc)
        duration_minutes = (
            int((end_utc - start_utc).total_seconds() / 60) if end_utc and start_utc else 0
        )

        attendees = raw.attendees or []
        is_internal = _all_internal_attendees(attendees)
        organizer_email = raw.organizer.get("email", "")
        response_status = "accepted"
        if attendees:
            response_status = attendees[0].get("responseStatus", "accepted")

        addresses = [a.get("email", "") for a in attendees if a.get("email")]
        if organizer_email:
            addresses.append(organizer_email)
        company_ids = await resolve_company_ids_for_addresses(
            self.db, self.tenant_id, addresses
        )

        await self.db.execute(
            sa_text("""
                INSERT INTO employee_calendar_events (
                    id, employee_id, tenant_id, provider, provider_event_id,
                    title, start_utc, end_utc, timezone_name, duration_minutes,
                    is_recurring, recurrence_rule, is_cancelled, is_all_day,
                    attendees_count, is_internal, conference_link, conference_provider,
                    organizer_email, response_status, location, description_md,
                    related_company_ids, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :employee_id, :tenant_id, 'google', :provider_event_id,
                    :title, :start_utc, :end_utc, :timezone_name, :duration_minutes,
                    :is_recurring, :recurrence_rule, false, :is_all_day,
                    :attendees_count, :is_internal, :conference_link, :conference_provider,
                    :organizer_email, :response_status, :location, :description_md,
                    CAST(:related_company_ids AS jsonb), now(), now()
                )
            """),
            {
                "employee_id": str(self.user_id),
                "tenant_id": str(self.tenant_id),
                "provider_event_id": raw.event_id,
                "title": raw.title or "",
                "start_utc": start_utc,
                "end_utc": end_utc,
                "timezone_name": raw.timezone_name or "",
                "duration_minutes": duration_minutes,
                "is_recurring": raw.is_recurring,
                "recurrence_rule": raw.recurrence_rule,
                "is_all_day": _is_all_day_event(raw),
                "attendees_count": len(attendees),
                "is_internal": is_internal,
                "conference_link": raw.conference_link or "",
                "conference_provider": raw.conference_provider or "",
                "organizer_email": organizer_email,
                "response_status": response_status,
                "location": raw.location or "",
                "description_md": raw.description or "",
                "related_company_ids": json.dumps(company_ids),
            },
        )

    async def _update_event(self, event_id: str, raw: RawCalendarEvent) -> None:
        await self.db.execute(
            sa_text("""
                UPDATE employee_calendar_events
                SET title = :title,
                    start_utc = :start_utc,
                    end_utc = :end_utc,
                    attendees_count = :attendees_count,
                    location = :location,
                    conference_link = :conference_link,
                    conference_provider = :conference_provider,
                    last_synced_at = now(),
                    updated_at = now()
                WHERE id = :id AND tenant_id = :tenant_id
            """),
            {
                "id": event_id,
                "tenant_id": str(self.tenant_id),
                "title": raw.title or "",
                "start_utc": raw.start_time,
                "end_utc": raw.end_time,
                "attendees_count": len(raw.attendees or []),
                "location": raw.location or "",
                "conference_link": raw.conference_link or "",
                "conference_provider": raw.conference_provider or "",
            },
        )

    async def _mark_cancelled(self, event_id: str) -> None:
        await self.db.execute(
            sa_text("""
                UPDATE employee_calendar_events
                SET is_cancelled = true,
                    last_synced_at = now(),
                    updated_at = now()
                WHERE id = :id AND tenant_id = :tenant_id
            """),
            {"id": event_id, "tenant_id": str(self.tenant_id)},
        )

    async def _get_existing_event(self, provider_event_id: str) -> dict | None:
        result = await self.db.execute(
            sa_text("""
                SELECT id FROM employee_calendar_events
                WHERE tenant_id = :tenant_id
                  AND provider = 'google'
                  AND provider_event_id = :event_id
                LIMIT 1
            """),
            {"tenant_id": str(self.tenant_id), "event_id": provider_event_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None


def _all_internal_attendees(attendees: list[dict]) -> bool:
    if not attendees:
        return True
    domains = set()
    for a in attendees:
        email = a.get("email", "")
        if "@" in email:
            domains.add(email.split("@")[1].lower())
    return len(domains) <= 1


def _is_all_day_event(raw: RawCalendarEvent) -> bool:
    if raw.start_time and raw.start_time.hour == 0 and raw.start_time.minute == 0:
        if raw.end_time and raw.end_time.hour == 0 and raw.end_time.minute == 0:
            diff = (raw.end_time - raw.start_time).total_seconds()
            if diff >= 86400:
                return True
    return False
