"""Google Calendar Provider — CalendarProvider implementation (ADR-012 §7, Phase 2).

Uses Google Calendar API via httpx.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from intelligence.activity_intelligence.contracts.models import RawCalendarEvent
from intelligence.activity_intelligence.contracts.provider import (
    CalendarProvider,
    ProviderProfile,
)


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar API provider using OAuth access tokens."""

    def __init__(self, credentials: dict | None = None):
        self._credentials = credentials or {}
        self._authenticated = False
        self._profile: ProviderProfile | None = None
        self._access_token: str | None = None

    async def authenticate(self, credentials: dict) -> bool:
        self._credentials = credentials
        token = credentials.get("access_token") or credentials.get("token")
        if not token:
            self._authenticated = False
            return False
        self._access_token = token
        self._authenticated = True
        self._profile = ProviderProfile(
            provider_id="google_calendar",
            provider_type="calendar",
            email=credentials.get("email", ""),
            display_name=credentials.get("display_name", ""),
            connected=True,
        )
        return True

    async def fetch_events(
        self, since: datetime, until: datetime
    ) -> list[RawCalendarEvent]:
        if not self._authenticated or not self._access_token:
            return []

        headers = {"Authorization": f"Bearer {self._access_token}"}
        params = {
            "timeMin": since.astimezone(timezone.utc).isoformat(),
            "timeMax": until.astimezone(timezone.utc).isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 250,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=headers,
                params=params,
            )
            if resp.status_code != 200:
                return []
            events: list[RawCalendarEvent] = []
            for item in resp.json().get("items", []):
                start = item.get("start", {})
                end = item.get("end", {})
                start_raw = start.get("dateTime") or start.get("date")
                end_raw = end.get("dateTime") or end.get("date")
                events.append(
                    RawCalendarEvent(
                        event_id=item.get("id", ""),
                        calendar_id="primary",
                        title=item.get("summary", ""),
                        description=item.get("description", "") or "",
                        location=item.get("location", "") or "",
                        start_time=datetime.fromisoformat(start_raw) if start_raw else None,
                        end_time=datetime.fromisoformat(end_raw) if end_raw else None,
                        attendees=[
                            {
                                "email": a.get("email", ""),
                                "displayName": a.get("displayName", ""),
                            }
                            for a in item.get("attendees", [])
                        ],
                        organizer={
                            "email": item.get("organizer", {}).get("email", ""),
                            "displayName": item.get("organizer", {}).get("displayName", ""),
                        },
                        is_recurring="recurringEventId" in item,
                        recurrence_rule=(item.get("recurrence") or [None])[0],
                        status=item.get("status", "confirmed"),
                    )
                )
            return events

    async def create_event(self, event: dict) -> str:
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        raise NotImplementedError("Calendar write requires calendar scope beyond readonly")

    async def update_event(self, event_id: str, updates: dict) -> bool:
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        raise NotImplementedError("Calendar write requires calendar scope beyond readonly")

    async def get_profile(self) -> ProviderProfile:
        return self._profile or ProviderProfile(
            provider_id="google_calendar",
            provider_type="calendar",
            connected=self._authenticated,
        )
