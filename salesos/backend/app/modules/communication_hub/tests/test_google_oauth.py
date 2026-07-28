"""Unit tests for Communication Hub — Google OAuth Service and Repository."""
import hashlib
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest

from app.modules.communication_hub.repository import GoogleAccountRepository
from app.modules.communication_hub.service import (
    GoogleOAuthService,
    GoogleOAuthError,
    GoogleTokenRefreshError,
    _OAUTH_STATE_STORE,
    _clean_expired_states,
    SCOPES,
)
from app.modules.communication_hub.models import GoogleAccount
from app.modules.communication_hub.schemas import (
    GoogleConnectResponse,
    GoogleStatusResponse,
    GoogleDisconnectResponse,
)


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------

class TestGoogleAccountRepository:
    def test_init(self):
        db = MagicMock()
        repo = GoogleAccountRepository(db)
        assert repo.db is db

    @pytest.mark.asyncio
    async def test_get_by_user_returns_account(self):
        db = AsyncMock()
        account = MagicMock(spec=GoogleAccount)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = account
        db.execute.return_value = result_mock

        repo = GoogleAccountRepository(db)
        result = await repo.get_by_user(uuid4(), uuid4())

        assert result is account
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user_returns_none(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        repo = GoogleAccountRepository(db)
        result = await repo.get_by_user(uuid4(), uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_create_account(self):
        db = AsyncMock()
        db.refresh = AsyncMock()

        repo = GoogleAccountRepository(db)
        account = await repo.create(
            tenant_id=uuid4(),
            user_id=uuid4(),
            email="test@gmail.com",
            access_token_encrypted="enc_access",
            refresh_token_encrypted="enc_refresh",
            token_expiry=datetime.now(timezone.utc),
            scope="openid email",
            google_user_id="123",
            avatar_url="https://example.com/avatar.jpg",
        )

        assert account is not None
        db.add.assert_called_once()
        db.flush.assert_called_once()
        db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.rowcount = 1
        db.execute.return_value = result_mock

        repo = GoogleAccountRepository(db)
        result = await repo.deactivate(uuid4(), uuid4())

        assert result is True
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_not_found(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.rowcount = 0
        db.execute.return_value = result_mock

        repo = GoogleAccountRepository(db)
        result = await repo.deactivate(uuid4(), uuid4())

        assert result is False


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestGoogleOAuthService:
    def setup_method(self):
        self.tenant_id = uuid4()
        self.user_id = uuid4()
        self.db = AsyncMock()

    def _make_service(self, **overrides):
        defaults = {
            "db": self.db,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
        }
        defaults.update(overrides)
        return GoogleOAuthService(**defaults)

    def test_generate_authorization_url(self):
        service = self._make_service()
        with patch("app.modules.communication_hub.service.settings") as mock_settings:
            mock_settings.sso_google_client_id = "test-client-id"
            mock_settings.next_public_api_url = "http://localhost:8000"

            auth_url, state = service.generate_authorization_url()

            assert "accounts.google.com" in auth_url
            assert "test-client-id" in auth_url
            assert "code" in auth_url
            assert state
            assert len(state) > 10

    def test_generate_authorization_url_stores_state(self):
        service = self._make_service()
        with patch("app.modules.communication_hub.service.settings") as mock_settings:
            mock_settings.sso_google_client_id = "test-client-id"
            mock_settings.next_public_api_url = "http://localhost:8000"

            _OAUTH_STATE_STORE.clear()
            auth_url, state = service.generate_authorization_url()
            state_hash = hashlib.sha256(state.encode()).hexdigest()

            assert state_hash in _OAUTH_STATE_STORE
            assert _OAUTH_STATE_STORE[state_hash]["tenant_id"] == str(self.tenant_id)
            assert _OAUTH_STATE_STORE[state_hash]["user_id"] == str(self.user_id)

            _OAUTH_STATE_STORE.clear()

    def test_generate_authorization_url_uses_custom_redirect(self):
        from urllib.parse import quote

        service = self._make_service()
        with patch("app.modules.communication_hub.service.settings") as mock_settings:
            mock_settings.sso_google_client_id = "test-client-id"
            mock_settings.google_redirect_uri = "https://custom.example.com/callback"

            auth_url, _ = service.generate_authorization_url()

            assert quote("https://custom.example.com/callback", safe="") in auth_url
            assert "redirect_uri=" in auth_url
            assert "access_type=offline" in auth_url

    def test_clean_expired_states(self):
        _OAUTH_STATE_STORE.clear()
        old_hash = "old_state_hash"
        _OAUTH_STATE_STORE[old_hash] = {
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "created_at": time.time() - 700,
        }
        new_hash = "new_state_hash"
        _OAUTH_STATE_STORE[new_hash] = {
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "created_at": time.time(),
        }

        _clean_expired_states()

        assert old_hash not in _OAUTH_STATE_STORE
        assert new_hash in _OAUTH_STATE_STORE
        _OAUTH_STATE_STORE.clear()

    @pytest.mark.asyncio
    async def test_handle_callback_invalid_state(self):
        service = self._make_service()
        with pytest.raises(GoogleOAuthError, match="Invalid or expired"):
            await service.handle_callback("fake_code", "fake_state")

    @pytest.mark.asyncio
    async def test_get_status_no_account(self):
        service = self._make_service()
        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=None)
        service.repo = repo

        connected, account = await service.get_status()

        assert connected is False
        assert account is None

    @pytest.mark.asyncio
    async def test_get_status_with_account(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        service.repo = repo

        connected, acc = await service.get_status()

        assert connected is True
        assert acc is account

    @pytest.mark.asyncio
    async def test_disconnect_no_account(self):
        service = self._make_service()
        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=None)
        service.repo = repo

        result = await service.disconnect()

        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_success(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.id = uuid4()
        repo = AsyncMock()
        repo.get_by_user = AsyncMock(return_value=account)
        repo.deactivate = AsyncMock(return_value=True)
        service.repo = repo

        result = await service.disconnect()

        assert result is True
        repo.deactivate.assert_called_once_with(account.id, self.tenant_id)

    @pytest.mark.asyncio
    async def test_get_valid_token_fresh(self):
        service = self._make_service()
        service._decrypt = MagicMock(return_value="raw_access_token")
        account = MagicMock(spec=GoogleAccount)
        account.access_token_encrypted = "enc_access"
        account.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        token = await service.get_valid_token(account)

        assert token == "raw_access_token"

    @pytest.mark.asyncio
    async def test_get_valid_token_expired_no_refresh(self):
        service = self._make_service()
        account = MagicMock(spec=GoogleAccount)
        account.token_expiry = datetime.now(timezone.utc) - timedelta(hours=1)
        account.refresh_token_encrypted = None

        with pytest.raises(GoogleTokenRefreshError, match="No refresh token"):
            await service.get_valid_token(account)

    @pytest.mark.asyncio
    async def test_scopes_defined(self):
        assert "openid" in SCOPES
        assert "email" in SCOPES
        assert "profile" in SCOPES
        assert "https://www.googleapis.com/auth/gmail.readonly" in SCOPES
        assert "https://www.googleapis.com/auth/calendar.readonly" in SCOPES
        assert len(SCOPES) == 5


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_google_connect_response(self):
        resp = GoogleConnectResponse(authorization_url="https://auth.example.com", state="abc123")
        assert resp.authorization_url == "https://auth.example.com"
        assert resp.state == "abc123"

    def test_google_status_response_disconnected(self):
        resp = GoogleStatusResponse(connected=False)
        assert resp.connected is False
        assert resp.account is None
        assert resp.scopes_granted == []
        assert resp.token_valid is False

    def test_google_disconnect_response(self):
        resp = GoogleDisconnectResponse(success=True, message="Done")
        assert resp.success is True
        assert resp.message == "Done"

    def test_google_callback_request_validation(self):
        from app.modules.communication_hub.schemas import GoogleCallbackRequest
        req = GoogleCallbackRequest(code="auth_code_123", state="state_abc")
        assert req.code == "auth_code_123"
        assert req.state == "state_abc"
