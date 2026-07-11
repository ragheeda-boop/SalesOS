from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.modules.sso.models import SSOConnection
from app.modules.sso.service import OAuthService
from app.modules.identity.models import User, Tenant


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def sso_service(mock_db):
    return OAuthService(db=mock_db, logger=None)


class TestSSOAuthorizationUrl:
    def test_get_authorization_url_google(self, sso_service):
        with patch("app.modules.sso.service.settings") as mock_settings:
            mock_settings.sso_google_client_id = "google-client-id"
            mock_settings.sso_google_client_secret = "google-secret"
            mock_settings.next_public_api_url = "http://localhost:8000"
            url = sso_service.get_authorization_url("google")
            assert "accounts.google.com" in url
            assert "client_id=google-client-id" in url
            assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fsso%2Fgoogle%2Fcallback" in url

    def test_get_authorization_url_microsoft(self, sso_service):
        with patch("app.modules.sso.service.settings") as mock_settings:
            mock_settings.sso_microsoft_client_id = "ms-client-id"
            mock_settings.next_public_api_url = "http://localhost:8000"
            url = sso_service.get_authorization_url("microsoft")
            assert "login.microsoftonline.com" in url

    def test_get_authorization_url_github(self, sso_service):
        with patch("app.modules.sso.service.settings") as mock_settings:
            mock_settings.sso_github_client_id = "gh-client-id"
            mock_settings.next_public_api_url = "http://localhost:8000"
            url = sso_service.get_authorization_url("github")
            assert "github.com/login/oauth/authorize" in url

    def test_get_authorization_url_invalid_provider(self, sso_service):
        with pytest.raises(ValueError, match="Unsupported provider"):
            sso_service.get_authorization_url("twitter")


class TestSSOCallback:
    @pytest.mark.asyncio
    async def test_handle_callback_existing_user(self, sso_service, mock_db):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        mock_user = User(id=user_id, tenant_id=tenant_id, email="test@example.com")

        mock_conn = SSOConnection(
            id="conn1", user_id=user_id, provider="google",
            provider_user_id="p1", provider_email="test@example.com",
        )
        conn_result = MagicMock()
        conn_result.scalar_one_or_none.return_value = mock_conn
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.side_effect = [conn_result, user_result]

        with patch.object(sso_service, "_exchange_code", new=AsyncMock(return_value={"access_token": "tok123", "expires_in": 3600})), \
             patch.object(sso_service, "_fetch_user_info", new=AsyncMock(return_value={"id": "p1", "email": "test@example.com", "name": "Test User"})):

            token, uid = await sso_service.handle_callback("google", "authcode123", "state123")
            assert token is not None
            assert uid == str(user_id)

    @pytest.mark.asyncio
    async def test_handle_callback_new_user(self, sso_service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [mock_result, mock_result]

        with patch.object(sso_service, "_exchange_code", new=AsyncMock(return_value={"access_token": "tok456", "expires_in": 3600})), \
             patch.object(sso_service, "_fetch_user_info", new=AsyncMock(return_value={"id": "gh456", "email": "new@example.com", "name": "New User"})), \
             patch("app.modules.sso.service.hash_password", return_value="hashed_pw"):

            token, uid = await sso_service.handle_callback("github", "authcode456", "state456")
            assert token is not None
            assert uid is not None

    @pytest.mark.asyncio
    async def test_handle_callback_no_email_github(self, sso_service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [mock_result, mock_result]

        with patch.object(sso_service, "_exchange_code", new=AsyncMock(return_value={"access_token": "tok789"})), \
             patch.object(sso_service, "_fetch_user_info", new=AsyncMock(return_value={"id": "gh789", "name": "No Email"})), \
             patch.object(sso_service, "_fetch_github_emails", new=AsyncMock(return_value=[{"email": "ghuser@github.com"}])), \
             patch("app.modules.sso.service.hash_password", return_value="hashed_pw"):

            token, uid = await sso_service.handle_callback("github", "code", "state")
            assert token is not None

    @pytest.mark.asyncio
    async def test_exchange_code_failure(self, sso_service):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("HTTP Error")
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value.post.return_value = mock_resp
        mock_client_instance.__aexit__.return_value = None

        with patch("httpx.AsyncClient", return_value=mock_client_instance):
            config = {
                "token_url": "https://example.com/token",
                "client_id": lambda: "id",
                "client_secret": lambda: "secret",
            }
            with pytest.raises(Exception):
                await sso_service._exchange_code("google", config, "bad-code")


class TestSSOConnections:
    @pytest.mark.asyncio
    async def test_get_connections_for_user(self, sso_service, mock_db):
        user_id = uuid.uuid4()
        mock_conn = SSOConnection(
            id="conn1", user_id=user_id, provider="google",
            provider_user_id="p1", provider_email="u@example.com",
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_conn]
        mock_db.execute.return_value = mock_result

        conns = await sso_service.get_connections_for_user(str(user_id))
        assert len(conns) == 1
        assert conns[0].provider == "google"

    @pytest.mark.asyncio
    async def test_disconnect_provider(self, sso_service, mock_db):
        user_id = uuid.uuid4()
        mock_conn = SSOConnection(
            id="conn1", user_id=user_id, provider="google",
            provider_user_id="p1", is_active=True,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_result

        result = await sso_service.disconnect_provider(str(user_id), "google")
        assert result is True
        assert mock_conn.is_active is False

    @pytest.mark.asyncio
    async def test_disconnect_provider_not_found(self, sso_service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await sso_service.disconnect_provider(str(uuid.uuid4()), "google")
        assert result is False
