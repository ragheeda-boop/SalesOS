"""Google Calendar Provider — CalendarProvider implementation (ADR-012 §7).

Uses Google Calendar REST API v3 via httpx to fetch events.
Authenticates with stored OAuth 2.0 access tokens.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from intelligence.activity_intelligence.contracts.models import RawCalendarEvent
from intelligence.activity_intelligence.contracts.provider import (
    CalendarProvider,
    ProviderProfile,
)

logger = logging.getLogger(__name__)

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


class CalendarAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Calendar API error {status}: {message}")


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar API provider using stored OAuth 2.0 tokens."""

    def __init__(self, access_token: str | None = None, email: str = ""):
        self._access_token = access_token
        self._email = email
        self._authenticated = bool(access_token)
        self._http = httpx.AsyncClient(timeout=30.0)
        self._profile = ProviderProfile(
            provider_id="google_calendar",
            provider_type="calendar",
            email=email,
            connected=bool(access_token),
        ) if access_token else None

    async def close(self) -> None:
        await self._http.aclose()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{CALENDAR_API_BASE}{path}"
        resp = await self._http.get(url, headers=self._headers(), params=params or {})
        if resp.status_code == 401:
            raise CalendarAPIError(401, "Token expired or revoked")
        if resp.status_code == 403:
            raise CalendarAPIError(403, "Insufficient permissions — calendar.readonly scope required")
        if resp.status_code == 410:
            raise CalendarAPIError(410, "Sync token expired — full re-sync required")
        if resp.status_code != 200:
            raise CalendarAPIError(resp.status_code, resp.text[:500])
        return resp.json()

    async def authenticate(self, credentials: dict) -> bool:
        self._access_token = credentials.get("access_token", "")
        self._email = credentials.get("email", "")
        self._authenticated = bool(self._access_token)
        if self._authenticated:
            self._profile = ProviderProfile(
                provider_id="google_calendar",
                provider_type="calendar",
                email=self._email,
                display_name=credentials.get("display_name", ""),
                connected=True,
            )
        return self._authenticated

    async def get_profile(self) -> ProviderProfile:
        if self._profile:
            return self._profile
        return ProviderProfile(
            provider_id="google_calendar", provider_type="calendar", connected=False
        )

    async def fetch_events(
        self, since: datetime | None = None, until: datetime | None = None,
        sync_token: str | None = None, max_results: int = 250,
    ) -> tuple[list[RawCalendarEvent], str | None]:
        """Fetch calendar events. Returns (events, next_sync_token).

        If sync_token is provided, uses incremental sync.
        Otherwise, uses time-based query.
        """
        if not self._authenticated:
            return [], None

        params: dict[str, Any] = {
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": min(max_results, 250),
        }

        if sync_token:
            params["syncToken"] = sync_token
        else:
            params["showDeleted"] = "true"
            if since:
                params["timeMin"] = since.isoformat()
            if until:
                params["timeMax"] = until.isoformat()

        data = await self._get("/calendars/primary/events", params)

        events: list[RawCalendarEvent] = []
        for item in data.get("items", []):
            raw = self._parse_event(item)
            if raw:
                events.append(raw)

        next_sync_token = data.get("nextSyncToken")
        return events, next_sync_token

    async def fetch_events_time_range(
        self, since: datetime, until: datetime, max_results: int = 250
    ) -> tuple[list[RawCalendarEvent], str | None]:
        """Fetch events in a specific time range (no sync token)."""
        return await self.fetch_events(since=since, until=until, max_results=max_results)

    async def create_event(self, event: dict) -> str:
        raise NotImplementedError("Calendar create not supported — readonly scope only")

    async def update_event(self, event_id: str, updates: dict) -> bool:
        raise NotImplementedError("Calendar update not supported — readonly scope only")

    async def get_profile_email(self) -> str:
        try:
            cal = await self._get("/calendars/primary", {})
            return cal.get("id", self._email)
        except CalendarAPIError:
            return self._email

    @staticmethod
    def _parse_event(item: dict) -> RawCalendarEvent | None:
        event_id = item.get("id", "")
        if not event_id:
            return None

        status = item.get("status", "confirmed")
        is_cancelled = status == "cancelled"

        start_data = item.get("start", {})
        end_data = item.get("end", {})
        start_str = start_data.get("dateTime") or start_data.get("date")
        end_str = end_data.get("dateTime") or end_data.get("date")

        start_time = _parse_datetime(start_str)
        end_time = _parse_datetime(end_str)
        is_all_day = "date" in start_data and "dateTime" not in start_data

        attendees = []
        for a in item.get("attendees", []):
            attendees.append({
                "email": a.get("email", ""),
                "displayName": a.get("displayName", ""),
                "responseStatus": a.get("responseStatus", "needsAction"),
                "organizer": a.get("self", False),
            })

        organizer = {}
        org_data = item.get("organizer", {})
        if org_data:
            organizer = {
                "email": org_data.get("email", ""),
                "displayName": org_data.get("displayName", ""),
            }

        recurrence = item.get("recurrence", [])
        recurrence_rule = recurrence[0] if recurrence else None
        is_recurring = bool(recurrence) or "recurringEventId" in item

        hangout_link = item.get("hangoutLink", "")
        conference_data = item.get("conferenceData", {})
        conference_link = hangout_link
        if not conference_link and conference_data:
            entry_points = conference_data.get("entryPoints", [])
            if entry_points:
                conference_link = entry_points[0].get("uri", "")

        conference_provider = ""
        if conference_data:
            conf_type = conference_data.get("conferenceSolution", {}).get("name", "")
            if "meet" in conf_type.lower():
                conference_provider = "google_meet"
            elif "zoom" in conf_type.lower():
                conference_provider = "zoom"
            elif "teams" in conf_type.lower():
                conference_provider = "teams"

        tz_start = start_data.get("timeZone", "")
        duration_minutes = 0
        if start_time and end_time:
            duration_minutes = int((end_time - start_time).total_seconds() / 60)

        created_at = _parse_datetime(item.get("created"))
        updated_at = _parse_datetime(item.get("updated"))

        return RawCalendarEvent(
            event_id=event_id,
            calendar_id="primary",
            title=item.get("summary", ""),
            description=item.get("description", ""),
            location=item.get("location", ""),
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            organizer=organizer,
            is_recurring=is_recurring,
            recurrence_rule=recurrence_rule,
            status="cancelled" if is_cancelled else status,
            conference_link=conference_link or "",
            conference_provider=conference_provider,
            timezone_name=tz_start or "",
            created_at=created_at,
            updated_at=updated_at,
        )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
