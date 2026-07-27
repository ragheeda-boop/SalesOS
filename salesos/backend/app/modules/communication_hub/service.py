"""Google OAuth Service — Communication Hub.

Handles the full OAuth2 Authorization Code Flow for Google Workspace:
- Authorization URL generation with CSRF state
- Token exchange and user info fetching
- Encrypted token storage
- Token refresh lifecycle
"""
import hashlib
import logging
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.communication_hub.models import GoogleAccount
from app.modules.communication_hub.repository import GoogleAccountRepository
from sdk.security import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

# In-memory state store (TTL 600s) — same pattern as SSO module
_OAUTH_STATE_STORE: dict[str, dict[str, Any]] = {}
_STATE_TTL = 600

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class GoogleOAuthError(Exception):
    pass


class GoogleTokenRefreshError(GoogleOAuthError):
    pass


def _clean_expired_states() -> None:
    now = time.time()
    expired = [k for k, v in _OAUTH_STATE_STORE.items() if now - v["created_at"] > _STATE_TTL]
    for k in expired:
        del _OAUTH_STATE_STORE[k]


def _get_encryption_key() -> str:
    key = getattr(settings, "google_encryption_key", None) or settings.secret_key
    return key


class GoogleOAuthService:
    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = GoogleAccountRepository(db)
        self._http = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._http.aclose()

    def _encrypt(self, plaintext: str) -> str:
        return encrypt_token(plaintext, _get_encryption_key())

    def _decrypt(self, ciphertext: str) -> str:
        return decrypt_token(ciphertext, _get_encryption_key())

    def _redirect_uri(self) -> str:
        base = getattr(settings, "google_redirect_uri", None)
        if base:
            return base
        api_url = getattr(settings, "next_public_api_url", "http://localhost:8000")
        return f"{api_url}/api/v1/integrations/google/callback"

    def generate_authorization_url(self) -> tuple[str, str]:
        _clean_expired_states()
        state = secrets.token_urlsafe(32)
        state_hash = hashlib.sha256(state.encode()).hexdigest()
        _OAUTH_STATE_STORE[state_hash] = {
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "created_at": time.time(),
        }

        params = {
            "client_id": settings.sso_google_client_id,
            "redirect_uri": self._redirect_uri(),
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{GOOGLE_AUTH_URL}?{query}"
        return auth_url, state

    async def handle_callback(self, code: str, state: str) -> GoogleAccount:
        state_hash = hashlib.sha256(state.encode()).hexdigest()
        state_data = _OAUTH_STATE_STORE.pop(state_hash, None)
        if not state_data:
            raise GoogleOAuthError("Invalid or expired OAuth state")

        tenant_id = UUID(state_data["tenant_id"])
        user_id = UUID(state_data["user_id"])

        tokens = await self._exchange_code(code)
        user_info = await self._fetch_user_info(tokens["access_token"])

        existing = await self.repo.get_by_user(tenant_id, user_id)
        access_enc = self._encrypt(tokens["access_token"])
        refresh_enc = self._encrypt(tokens["refresh_token"]) if tokens.get("refresh_token") else None
        expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))

        if existing:
            await self.repo.update_tokens(
                existing.id, access_enc, refresh_enc, expiry
            )
            await self.db.commit()
            await self.db.refresh(existing)
            logger.info(
                "google_account.tokens_updated",
                extra={"tenant_id": str(tenant_id), "email": user_info.get("email")},
            )
            return existing

        account = await self.repo.create(
            tenant_id=tenant_id,
            user_id=user_id,
            email=user_info.get("email", ""),
            access_token_encrypted=access_enc,
            refresh_token_encrypted=refresh_enc,
            token_expiry=expiry,
            scope=" ".join(SCOPES),
            google_user_id=user_info.get("id"),
            avatar_url=user_info.get("picture"),
        )
        await self.db.commit()
        return account

    async def _exchange_code(self, code: str) -> dict[str, Any]:
        data = {
            "code": code,
            "client_id": settings.sso_google_client_id,
            "client_secret": settings.sso_google_client_secret,
            "redirect_uri": self._redirect_uri(),
            "grant_type": "authorization_code",
        }
        resp = await self._http.post(GOOGLE_TOKEN_URL, data=data)
        if resp.status_code != 200:
            logger.error("google_token_exchange.failed", extra={"status": resp.status_code, "body": resp.text})
            raise GoogleOAuthError(f"Token exchange failed: {resp.status_code}")
        return resp.json()

    async def _fetch_user_info(self, access_token: str) -> dict[str, Any]:
        resp = await self._http.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            raise GoogleOAuthError(f"User info fetch failed: {resp.status_code}")
        return resp.json()

    async def get_valid_token(self, account: GoogleAccount) -> str:
        if account.token_expiry and account.token_expiry > datetime.now(timezone.utc):
            return self._decrypt(account.access_token_encrypted)

        if not account.refresh_token_encrypted:
            raise GoogleTokenRefreshError("No refresh token available")

        refresh_token = self._decrypt(account.refresh_token_encrypted)
        new_tokens = await self._refresh_access_token(refresh_token)

        access_enc = self._encrypt(new_tokens["access_token"])
        refresh_enc = self._encrypt(new_tokens["refresh_token"]) if new_tokens.get("refresh_token") else None
        expiry = datetime.now(timezone.utc) + timedelta(seconds=new_tokens.get("expires_in", 3600))

        await self.repo.update_tokens(account.id, access_enc, refresh_enc, expiry)
        await self.db.commit()

        return new_tokens["access_token"]

    async def _refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        data = {
            "client_id": settings.sso_google_client_id,
            "client_secret": settings.sso_google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = await self._http.post(GOOGLE_TOKEN_URL, data=data)
        if resp.status_code != 200:
            logger.error("google_token_refresh.failed", extra={"status": resp.status_code})
            raise GoogleTokenRefreshError(f"Token refresh failed: {resp.status_code}")
        return resp.json()

    async def get_status(self) -> tuple[bool, GoogleAccount | None]:
        account = await self.repo.get_by_user(self.tenant_id, self.user_id)
        if not account:
            return False, None

        token_valid = False
        if account.token_expiry:
            token_valid = account.token_expiry > datetime.now(timezone.utc)

        return True, account

    async def disconnect(self) -> bool:
        account = await self.repo.get_by_user(self.tenant_id, self.user_id)
        if not account:
            return False
        return await self.repo.deactivate(account.id, self.tenant_id)
