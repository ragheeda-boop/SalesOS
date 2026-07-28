"""Outlook / Microsoft 365 providers — future-compatible stubs with real Graph paths.

These implement the EmailProvider / CalendarProvider ABCs so Outlook can be
swapped in without changing Activity Intelligence engines.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from intelligence.activity_intelligence.contracts.models import RawCalendarEvent, RawEmail
from intelligence.activity_intelligence.contracts.provider import (
    CalendarProvider,
    EmailProvider,
    ProviderProfile,
)


class OutlookEmailProvider(EmailProvider):
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
            provider_id="outlook",
            provider_type="email",
            email=credentials.get("email", ""),
            display_name=credentials.get("display_name", ""),
            connected=True,
        )
        return True

    async def fetch_emails(
        self, since: datetime | None = None, max_results: int = 50
    ) -> list[RawEmail]:
        if not self._authenticated or not self._access_token:
            return []
        params: dict = {"$top": max_results, "$orderby": "receivedDateTime desc"}
        if since:
            params["$filter"] = f"receivedDateTime ge {since.astimezone(timezone.utc).isoformat()}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers=headers,
                params=params,
            )
            if resp.status_code != 200:
                return []
            emails: list[RawEmail] = []
            for msg in resp.json().get("value", []):
                received = msg.get("receivedDateTime")
                emails.append(
                    RawEmail(
                        message_id=msg.get("id", ""),
                        thread_id=msg.get("conversationId"),
                        subject=msg.get("subject", "") or "",
                        from_address=(msg.get("from") or {}).get("emailAddress", {}).get("address", ""),
                        to_addresses=[
                            r.get("emailAddress", {}).get("address", "")
                            for r in msg.get("toRecipients", [])
                        ],
                        body_text=msg.get("bodyPreview", "") or "",
                        received_at=datetime.fromisoformat(received.replace("Z", "+00:00")) if received else None,
                    )
                )
            return emails

    async def fetch_thread(self, thread_id: str) -> list[RawEmail]:
        return []

    async def send_email(self, to: str, subject: str, body: str) -> str:
        raise NotImplementedError("Outlook send not enabled in current scopes")

    async def get_profile(self) -> ProviderProfile:
        return self._profile or ProviderProfile(
            provider_id="outlook",
            provider_type="email",
            connected=self._authenticated,
        )


class OutlookCalendarProvider(CalendarProvider):
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
            provider_id="outlook_calendar",
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
            "startDateTime": since.astimezone(timezone.utc).isoformat(),
            "endDateTime": until.astimezone(timezone.utc).isoformat(),
            "$top": 250,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me/calendarView",
                headers=headers,
                params=params,
            )
            if resp.status_code != 200:
                return []
            events: list[RawCalendarEvent] = []
            for item in resp.json().get("value", []):
                start = (item.get("start") or {}).get("dateTime")
                end = (item.get("end") or {}).get("dateTime")
                events.append(
                    RawCalendarEvent(
                        event_id=item.get("id", ""),
                        title=item.get("subject", "") or "",
                        description=item.get("bodyPreview", "") or "",
                        location=(item.get("location") or {}).get("displayName", "") or "",
                        start_time=datetime.fromisoformat(start + "Z") if start else None,
                        end_time=datetime.fromisoformat(end + "Z") if end else None,
                        attendees=[
                            {
                                "email": a.get("emailAddress", {}).get("address", ""),
                                "displayName": a.get("emailAddress", {}).get("name", ""),
                            }
                            for a in item.get("attendees", [])
                        ],
                        organizer={
                            "email": (item.get("organizer") or {}).get("emailAddress", {}).get("address", ""),
                        },
                        is_recurring=item.get("type") == "seriesMaster",
                        status="cancelled" if item.get("isCancelled") else "confirmed",
                    )
                )
            return events

    async def create_event(self, event: dict) -> str:
        raise NotImplementedError("Outlook calendar write not enabled")

    async def update_event(self, event_id: str, updates: dict) -> bool:
        raise NotImplementedError("Outlook calendar write not enabled")

    async def get_profile(self) -> ProviderProfile:
        return self._profile or ProviderProfile(
            provider_id="outlook_calendar",
            provider_type="calendar",
            connected=self._authenticated,
        )
