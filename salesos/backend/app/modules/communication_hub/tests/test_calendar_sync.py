"""Unit tests for Calendar Sync Service and Google Calendar Provider."""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.communication_hub.calendar_sync import (
    CalendarSyncService,
    CalendarSyncError,
    _all_internal_attendees,
    _is_all_day_event,
)
from app.modules.communication_hub.models import GoogleAccount
from intelligence.activity_intelligence.providers.google.calendar_provider import (
    GoogleCalendarProvider,
    CalendarAPIError,
    _parse_datetime,
)
from intelligence.activity_intelligence.contracts.models import RawCalendarEvent


# ---------------------------------------------------------------------------
# GoogleCalendarProvider tests
# ---------------------------------------------------------------------------

class TestGoogleCalendarProvider:
    def test_init(self):
        provider = GoogleCalendarProvider(access_token="tok_123", email="test@gmail.com")
        assert provider._access_token == "tok_123"
        assert provider._authenticated is True
        assert provider._profile.connected is True

    def test_init_no_token(self):
        provider = GoogleCalendarProvider()
        assert provider._authenticated is False
        assert provider._profile is None

    @pytest.mark.asyncio
    async def test_authenticate(self):
        provider = GoogleCalendarProvider()
        result = await provider.authenticate({"access_token": "tok", "email": "a@b.com"})
        assert result is True
        assert provider._authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_empty_token(self):
        provider = GoogleCalendarProvider()
        result = await provider.authenticate({"access_token": ""})
        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_events_not_authenticated(self):
        provider = GoogleCalendarProvider()
        events, token = await provider.fetch_events(since=datetime.now(timezone.utc))
        assert events == []
        assert token is None

    @pytest.mark.asyncio
    async def test_create_event_raises(self):
        provider = GoogleCalendarProvider(access_token="tok")
        with pytest.raises(NotImplementedError):
            await provider.create_event({})

    @pytest.mark.asyncio
    async def test_update_event_raises(self):
        provider = GoogleCalendarProvider(access_token="tok")
        with pytest.raises(NotImplementedError):
            await provider.update_event("eid", {})

    @pytest.mark.asyncio
    async def test_get_profile_cached(self):
        provider = GoogleCalendarProvider(access_token="tok", email="cached@gmail.com")
        profile = await provider.get_profile()
        assert profile.email == "cached@gmail.com"
        assert profile.connected is True

    @pytest.mark.asyncio
    async def test_close(self):
        provider = GoogleCalendarProvider(access_token="tok")
        await provider.close()

    def test_parse_event_complete(self):
        item = {
            "id": "evt_123",
            "summary": "Team Meeting",
            "description": "Weekly standup",
            "location": "Room A",
            "status": "confirmed",
            "start": {"dateTime": "2026-07-28T10:00:00+03:00", "timeZone": "Asia/Amman"},
            "end": {"dateTime": "2026-07-28T11:00:00+03:00", "timeZone": "Asia/Amman"},
            "attendees": [
                {"email": "a@company.com", "displayName": "Alice", "responseStatus": "accepted", "self": False},
                {"email": "b@company.com", "displayName": "Bob", "responseStatus": "tentative", "self": True},
            ],
            "organizer": {"email": "a@company.com", "displayName": "Alice"},
            "recurrence": ["RRULE:FREQ=WEEKLY"],
            "hangoutLink": "https://meet.google.com/abc-defg",
            "conferenceData": {"conferenceSolution": {"name": "Google Meet"}},
            "created": "2026-07-20T08:00:00Z",
            "updated": "2026-07-27T15:00:00Z",
        }
        raw = GoogleCalendarProvider._parse_event(item)
        assert raw is not None
        assert raw.event_id == "evt_123"
        assert raw.title == "Team Meeting"
        assert raw.description == "Weekly standup"
        assert raw.location == "Room A"
        assert raw.is_recurring is True
        assert raw.recurrence_rule == "RRULE:FREQ=WEEKLY"
        assert len(raw.attendees) == 2
        assert raw.organizer["email"] == "a@company.com"
        assert raw.conference_link == "https://meet.google.com/abc-defg"
        assert raw.conference_provider == "google_meet"

    def test_parse_event_cancelled(self):
        item = {"id": "evt_cancel", "status": "cancelled", "start": {"dateTime": "2026-07-28T10:00:00Z"}, "end": {"dateTime": "2026-07-28T11:00:00Z"}}
        raw = GoogleCalendarProvider._parse_event(item)
        assert raw is not None
        assert raw.status == "cancelled"

    def test_parse_event_all_day(self):
        item = {"id": "evt_allday", "summary": "Holiday", "start": {"date": "2026-07-28"}, "end": {"date": "2026-07-29"}, "attendees": [], "status": "confirmed"}
        raw = GoogleCalendarProvider._parse_event(item)
        assert raw is not None
        assert raw.start_time is not None

    def test_parse_event_no_id(self):
        raw = GoogleCalendarProvider._parse_event({})
        assert raw is None


class TestParseDatetime:
    def test_parse_iso(self):
        dt = _parse_datetime("2026-07-28T10:00:00+03:00")
        assert dt is not None
        assert dt.year == 2026

    def test_parse_z_suffix(self):
        dt = _parse_datetime("2026-07-28T10:00:00Z")
        assert dt is not None
        assert dt.tzinfo is not None

    def test_parse_none(self):
        assert _parse_datetime(None) is None

    def test_parse_empty(self):
        assert _parse_datetime("") is None

    def test_parse_invalid(self):
        assert _parse_datetime("not-a-date") is None


# ---------------------------------------------------------------------------
# CalendarSyncService tests
# ---------------------------------------------------------------------------

class TestCalendarSyncService:
    def setup_method(self):
        self.tenant_id = uuid4()
        self.user_id = uuid4()
        self.db = AsyncMock()

    def _make_service(self):
        return CalendarSyncService(self.db, self.tenant_id, self.user_id)

    @pytest.mark.asyncio
    async def test_sync_no_account(self):
        service = self._make_service()
        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=None)
        service.repo = repo

        with pytest.raises(CalendarSyncError, match="No active Google account"):
            await service.sync()

    @pytest.mark.asyncio
    async def test_sync_initial_flow(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        account.email = "test@gmail.com"
        account.calendar_sync_token = None

        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        repo.update_calendar_sync_token = AsyncMock()
        repo.update_last_sync = AsyncMock()
        service.repo = repo

        mock_provider = AsyncMock()
        mock_provider.fetch_events_time_range = AsyncMock(return_value=([
            RawCalendarEvent(
                event_id="evt_1",
                title="Meeting",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc) + timedelta(hours=1),
                status="confirmed",
            )
        ], "next_token_123"))
        mock_provider.close = AsyncMock()

        with patch.object(service, '_ensure_provider', return_value=mock_provider):
            with patch.object(service, '_get_existing_event', return_value=None):
                with patch.object(service, '_insert_event', new_callable=AsyncMock) as mock_insert:
                    result = await service.sync(days_lookback=30, days_forward=30)

                    assert result["synced_count"] == 1
                    assert result["new_count"] == 1
                    assert result["next_sync_token"] == "next_token_123"
                    mock_insert.assert_called_once()
                    repo.update_calendar_sync_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_handles_existing_event(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        account.email = "test@gmail.com"
        account.calendar_sync_token = None

        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        repo.update_calendar_sync_token = AsyncMock()
        repo.update_last_sync = AsyncMock()
        service.repo = repo

        mock_provider = AsyncMock()
        mock_provider.fetch_events_time_range = AsyncMock(return_value=([
            RawCalendarEvent(
                event_id="evt_existing",
                title="Updated Meeting",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc) + timedelta(hours=1),
                status="confirmed",
            )
        ], None))
        mock_provider.close = AsyncMock()

        with patch.object(service, '_ensure_provider', return_value=mock_provider):
            with patch.object(service, '_get_existing_event', return_value={"id": str(uuid4())}):
                with patch.object(service, '_update_event', new_callable=AsyncMock) as mock_update:
                    result = await service.sync()
                    assert result["updated_count"] == 1
                    mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_handles_cancelled_event(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        account.email = "test@gmail.com"
        account.calendar_sync_token = None

        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        repo.update_calendar_sync_token = AsyncMock()
        repo.update_last_sync = AsyncMock()
        service.repo = repo

        mock_provider = AsyncMock()
        mock_provider.fetch_events_time_range = AsyncMock(return_value=([
            RawCalendarEvent(
                event_id="evt_cancel",
                title="Cancelled",
                status="cancelled",
            )
        ], None))
        mock_provider.close = AsyncMock()

        with patch.object(service, '_ensure_provider', return_value=mock_provider):
            with patch.object(service, '_get_existing_event', return_value={"id": str(uuid4())}):
                with patch.object(service, '_mark_cancelled', new_callable=AsyncMock) as mock_cancel:
                    result = await service.sync()
                    assert result["cancelled_count"] == 1
                    mock_cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_uses_incremental_token(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        account.email = "test@gmail.com"
        account.calendar_sync_token = "existing_token"

        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        repo.update_calendar_sync_token = AsyncMock()
        repo.update_last_sync = AsyncMock()
        service.repo = repo

        mock_provider = AsyncMock()
        mock_provider.fetch_events = AsyncMock(return_value=([], "newer_token"))
        mock_provider.close = AsyncMock()

        with patch.object(service, '_ensure_provider', return_value=mock_provider):
            result = await service.sync()
            mock_provider.fetch_events.assert_called_once()
            assert result["next_sync_token"] == "newer_token"
            repo.update_calendar_sync_token.assert_called_once()
            mock_provider.fetch_events_time_range.assert_not_called()


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_all_internal_attendees_empty(self):
        assert _all_internal_attendees([]) is True

    def test_all_internal_attendees_same_domain(self):
        attendees = [{"email": "a@company.com"}, {"email": "b@company.com"}]
        assert _all_internal_attendees(attendees) is True

    def test_all_internal_attendees_different_domains(self):
        attendees = [{"email": "a@company.com"}, {"email": "b@external.com"}]
        assert _all_internal_attendees(attendees) is False

    def test_is_all_day_event(self):
        raw = RawCalendarEvent(
            event_id="1",
            start_time=datetime(2026, 7, 28, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 7, 29, 0, 0, tzinfo=timezone.utc),
        )
        assert _is_all_day_event(raw) is True

    def test_is_not_all_day_event(self):
        raw = RawCalendarEvent(
            event_id="1",
            start_time=datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 7, 28, 11, 0, tzinfo=timezone.utc),
        )
        assert _is_all_day_event(raw) is False


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestCalendarSchemas:
    def test_calendar_sync_request_defaults(self):
        from app.modules.communication_hub.schemas import GoogleCalendarSyncRequest
        req = GoogleCalendarSyncRequest()
        assert req.days_lookback == 90
        assert req.days_forward == 90

    def test_calendar_sync_request_custom(self):
        from app.modules.communication_hub.schemas import GoogleCalendarSyncRequest
        req = GoogleCalendarSyncRequest(days_lookback=30, days_forward=60)
        assert req.days_lookback == 30
        assert req.days_forward == 60

    def test_calendar_sync_response(self):
        from app.modules.communication_hub.schemas import GoogleCalendarSyncResponse
        resp = GoogleCalendarSyncResponse(
            success=True,
            synced_count=5,
            new_count=3,
            updated_count=1,
            cancelled_count=1,
            message="Done",
        )
        assert resp.success is True
        assert resp.cancelled_count == 1
        assert resp.errors == []
