"""Unit tests for Gmail Sync Service and Gmail Provider."""
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.communication_hub.gmail_sync import (
    GmailSyncService,
    GmailSyncError,
)
from app.modules.communication_hub.models import GoogleAccount
from intelligence.activity_intelligence.providers.google.gmail_provider import (
    GoogleGmailProvider,
    GmailAPIError,
)
from intelligence.activity_intelligence.contracts.models import RawEmail


# ---------------------------------------------------------------------------
# GoogleGmailProvider tests
# ---------------------------------------------------------------------------

class TestGoogleGmailProvider:
    def test_init(self):
        provider = GoogleGmailProvider(access_token="tok_123", email="test@gmail.com")
        assert provider._access_token == "tok_123"
        assert provider._email == "test@gmail.com"
        assert provider._authenticated is True

    def test_init_no_token(self):
        provider = GoogleGmailProvider()
        assert provider._authenticated is False

    @pytest.mark.asyncio
    async def test_authenticate(self):
        provider = GoogleGmailProvider()
        result = await provider.authenticate({"access_token": "tok", "email": "a@b.com"})
        assert result is True
        assert provider._authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_empty_token(self):
        provider = GoogleGmailProvider()
        result = await provider.authenticate({"access_token": ""})
        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_emails_not_authenticated(self):
        provider = GoogleGmailProvider()
        result = await provider.fetch_emails()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_thread_not_authenticated(self):
        provider = GoogleGmailProvider()
        result = await provider.fetch_thread("thread_123")
        assert result == []

    @pytest.mark.asyncio
    async def test_send_email_raises(self):
        provider = GoogleGmailProvider(access_token="tok")
        with pytest.raises(NotImplementedError):
            await provider.send_email("to@test.com", "subj", "body")

    @pytest.mark.asyncio
    async def test_get_profile_cached(self):
        provider = GoogleGmailProvider(access_token="tok", email="cached@gmail.com")
        profile = await provider.get_profile()
        assert profile.email == "cached@gmail.com"
        assert profile.connected is True

    @pytest.mark.asyncio
    async def test_close(self):
        provider = GoogleGmailProvider(access_token="tok")
        await provider.close()

    def test_parse_headers(self):
        headers = [
            {"name": "From", "value": "sender@test.com"},
            {"name": "Subject", "value": "Hello"},
        ]
        result = GoogleGmailProvider._parse_headers(headers)
        assert result["From"] == "sender@test.com"
        assert result["Subject"] == "Hello"

    def test_extract_body_text(self):
        import base64
        payload = {
            "mimeType": "text/plain",
            "body": {"data": base64.urlsafe_b64encode(b"Hello World").decode()},
            "parts": [],
        }
        text, html = GoogleGmailProvider._extract_body(payload)
        assert text == "Hello World"
        assert html == ""

    def test_extract_body_multipart(self):
        import base64
        payload = {
            "mimeType": "multipart/alternative",
            "body": {},
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": base64.urlsafe_b64encode(b"plain text").decode()},
                    "parts": [],
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": base64.urlsafe_b64encode(b"<p>html</p>").decode()},
                    "parts": [],
                },
            ],
        }
        text, html = GoogleGmailProvider._extract_body(payload)
        assert text == "plain text"
        assert html == "<p>html</p>"

    def test_parse_address_list(self):
        assert GoogleGmailProvider._parse_address_list("") == []
        assert GoogleGmailProvider._parse_address_list("a@test.com") == ["a@test.com"]
        assert GoogleGmailProvider._parse_address_list("a@test.com, b@test.com") == [
            "a@test.com",
            "b@test.com",
        ]

    def test_has_attachments_true(self):
        payload = {"filename": "report.pdf", "body": {}, "parts": []}
        assert GoogleGmailProvider._has_attachments(payload) is True

    def test_has_attachments_nested(self):
        payload = {
            "filename": "",
            "body": {},
            "parts": [{"filename": "data.csv", "body": {}, "parts": []}],
        }
        assert GoogleGmailProvider._has_attachments(payload) is True

    def test_has_attachments_false(self):
        payload = {"filename": "", "body": {}, "parts": []}
        assert GoogleGmailProvider._has_attachments(payload) is False

    def test_determine_direction_outbound(self):
        raw = RawEmail(message_id="1", from_address="me@company.com")
        direction = GmailSyncService._determine_direction(raw, "me@company.com")
        assert direction == "outbound"

    def test_determine_direction_inbound(self):
        raw = RawEmail(message_id="1", from_address="someone@other.com")
        direction = GmailSyncService._determine_direction(raw, "me@company.com")
        assert direction == "inbound"


# ---------------------------------------------------------------------------
# GmailSyncService tests
# ---------------------------------------------------------------------------

class TestGmailSyncService:
    def setup_method(self):
        self.tenant_id = uuid4()
        self.user_id = uuid4()
        self.db = AsyncMock()

    def _make_service(self):
        return GmailSyncService(self.db, self.tenant_id, self.user_id)

    @pytest.mark.asyncio
    async def test_sync_no_account(self):
        service = self._make_service()
        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=None)
        service.repo = repo

        with pytest.raises(GmailSyncError, match="No active Google account"):
            await service.sync()

    @pytest.mark.asyncio
    async def test_sync_initial_flow(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        account.history_id = None
        account.email = "test@gmail.com"
        account.last_sync_at = None

        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        service.repo = repo

        mock_provider = AsyncMock()
        mock_provider.fetch_emails = AsyncMock(return_value=[
            RawEmail(
                message_id="msg_1",
                subject="Test",
                from_address="sender@test.com",
                to_addresses=["test@gmail.com"],
                sent_at=datetime.now(timezone.utc),
                labels=["INBOX"],
            )
        ])
        mock_provider.get_history_id = AsyncMock(return_value="12345")
        mock_provider.close = AsyncMock()

        with patch.object(service, '_ensure_provider', return_value=mock_provider):
            with patch.object(service, '_get_existing_email', return_value=None):
                with patch.object(service, '_insert_email', new_callable=AsyncMock) as mock_insert:
                    result = await service.sync(days_lookback=7, max_results=50)

                    assert result["synced_count"] == 1
                    assert result["new_count"] == 1
                    assert result["updated_count"] == 0
                    mock_insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_incremental_flow(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        account.history_id = "99999"
        account.email = "test@gmail.com"

        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        service.repo = repo

        raw = RawEmail(
            message_id="msg_2",
            subject="Inc",
            from_address="a@b.com",
            sent_at=datetime.now(timezone.utc),
            labels=["INBOX"],
        )

        mock_provider = AsyncMock()
        mock_provider.fetch_history = AsyncMock(return_value={
            "history": [{"messagesAdded": [{"message": {"id": "msg_2"}}]}],
            "historyId": "100000",
        })
        mock_provider.fetch_message = AsyncMock(return_value=raw)
        mock_provider.get_history_id = AsyncMock(return_value="100000")
        mock_provider.close = AsyncMock()

        with patch.object(service, '_ensure_provider', return_value=mock_provider):
            with patch.object(service, '_get_existing_email', return_value=None):
                with patch.object(service, '_insert_email', new_callable=AsyncMock):
                    result = await service.sync()

                    assert result["synced_count"] == 1
                    mock_provider.fetch_history.assert_called_once_with("99999")

    @pytest.mark.asyncio
    async def test_sync_updates_existing_email(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        account.history_id = None
        account.email = "test@gmail.com"

        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        service.repo = repo

        raw = RawEmail(
            message_id="msg_3",
            subject="Existing",
            from_address="sender@test.com",
            sent_at=datetime.now(timezone.utc),
            labels=["INBOX"],
        )

        mock_provider = AsyncMock()
        mock_provider.fetch_emails = AsyncMock(return_value=[raw])
        mock_provider.get_history_id = AsyncMock(return_value="500")
        mock_provider.close = AsyncMock()

        with patch.object(service, '_ensure_provider', return_value=mock_provider):
            with patch.object(service, '_get_existing_email', return_value={"id": str(uuid4())}):
                with patch.object(service, '_update_email', new_callable=AsyncMock) as mock_update:
                    result = await service.sync()

                    assert result["updated_count"] == 1
                    assert result["new_count"] == 0
                    mock_update.assert_called_once()


# ---------------------------------------------------------------------------
# Schema tests for new sync schemas
# ---------------------------------------------------------------------------

class TestSyncSchemas:
    def test_sync_request_defaults(self):
        from app.modules.communication_hub.schemas import GoogleSyncRequest
        req = GoogleSyncRequest()
        assert req.days_lookback == 30
        assert req.max_results == 100

    def test_sync_request_custom(self):
        from app.modules.communication_hub.schemas import GoogleSyncRequest
        req = GoogleSyncRequest(days_lookback=7, max_results=50)
        assert req.days_lookback == 7
        assert req.max_results == 50

    def test_sync_response(self):
        from app.modules.communication_hub.schemas import GoogleSyncResponse
        resp = GoogleSyncResponse(
            success=True,
            synced_count=10,
            new_count=8,
            updated_count=2,
            message="Done",
        )
        assert resp.success is True
        assert resp.synced_count == 10
        assert resp.new_count == 8
        assert resp.updated_count == 2
        assert resp.errors == []
