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
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.oauth_state import (
    clear_oauth_state_memory,
    get_oauth_state,
    memory_store_snapshot,
    store_oauth_state,
)
from app.config import settings
from app.modules.communication_hub.models import GoogleAccount
from app.modules.communication_hub.repository import GoogleAccountRepository
from sdk.security import decrypt_token, encrypt_token

# Refresh access token this many seconds before hard expiry.
_TOKEN_EXPIRY_SKEW_SECONDS = 60

logger = logging.getLogger(__name__)

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


class _MemoryStateFacade(dict):
    """Mutable dict facade so existing unit tests can inspect/clear OAuth state."""

    def clear(self) -> None:  # type: ignore[override]
        clear_oauth_state_memory()
        super().clear()

    def __setitem__(self, key: str, value: Any) -> None:
        store_oauth_state(key, value, ttl=_STATE_TTL)
        super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        get_oauth_state(key, consume=True)
        super().pop(key, None)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return get_oauth_state(key, consume=False) is not None

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        val = get_oauth_state(key, consume=False)
        return default if val is None else val

    def pop(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        val = get_oauth_state(key, consume=True)
        super().pop(key, None)
        return default if val is None else val


_OAUTH_STATE_STORE = _MemoryStateFacade()


def _clean_expired_states() -> None:
    """Drop entries whose payload ``created_at`` exceeds TTL (Redis keys deleted too)."""
    now = time.time()
    for key, value in list(memory_store_snapshot().items()):
        if isinstance(value, dict):
            created = float(value.get("created_at") or now)
            if now - created > _STATE_TTL:
                get_oauth_state(key, consume=True)
                dict.pop(_OAUTH_STATE_STORE, key, None)


def google_oauth_config_status() -> tuple[bool, list[str]]:
    """Return (configured, missing_env_names) without exposing secret values."""
    missing: list[str] = []
    if not (getattr(settings, "sso_google_client_id", None) or "").strip():
        missing.append("SSO_GOOGLE_CLIENT_ID")
    if not (getattr(settings, "sso_google_client_secret", None) or "").strip():
        missing.append("SSO_GOOGLE_CLIENT_SECRET")
    if not (getattr(settings, "google_encryption_key", None) or "").strip():
        missing.append("GOOGLE_ENCRYPTION_KEY")
    # redirect URI has a safe default from next_public_api_url — not required
    return (len(missing) == 0, missing)


def _get_encryption_key() -> str:
    """OAuth token encryption key — must not reuse JWT/app secret_key."""
    key = (getattr(settings, "google_encryption_key", None) or "").strip()

    if key:
        return key
    env = (settings.env or "").lower()
    if env in ("production", "prod", "staging"):
        raise GoogleOAuthError(
            "GOOGLE_ENCRYPTION_KEY must be set in staging/production "
            "(must not fall back to SECRET_KEY)"
        )
    # Local/dev only — still avoid silent reuse of JWT signing material.
    raise GoogleOAuthError("GOOGLE_ENCRYPTION_KEY is required to encrypt Google OAuth tokens")


def _get_previous_encryption_keys() -> list[str]:
    """Optional previous keys for decrypt during key rotation (comma-separated)."""
    raw = (getattr(settings, "google_encryption_key_previous", None) or "").strip()
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


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
        """Decrypt with current key; fall back to previous keys during rotation."""
        keys = [_get_encryption_key(), *_get_previous_encryption_keys()]
        last_err: Exception | None = None
        for key in keys:
            try:
                return decrypt_token(ciphertext, key)
            except Exception as exc:  # InvalidToken or key mismatch
                last_err = exc
                continue
        if last_err:
            raise last_err
        raise GoogleOAuthError("Token decrypt failed")

    def _redirect_uri(self) -> str:
        base = cast(str | None, getattr(settings, "google_redirect_uri", None))
        if base:
            return base
        api_url = cast(str, getattr(settings, "next_public_api_url", "http://localhost:8000"))
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
        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
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
        refresh_enc = (
            self._encrypt(tokens["refresh_token"]) if tokens.get("refresh_token") else None
        )
        expiry = datetime.now(UTC) + timedelta(seconds=tokens.get("expires_in", 3600))

        if existing:
            await self.repo.update_tokens(
                existing.id, access_enc, refresh_enc, expiry, tenant_id=tenant_id
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
            logger.error(
                "google_token_exchange.failed",
                extra={"status": resp.status_code, "body": resp.text},
            )
            raise GoogleOAuthError(f"Token exchange failed: {resp.status_code}")
        return cast(dict[str, Any], resp.json())

    async def _fetch_user_info(self, access_token: str) -> dict[str, Any]:
        resp = await self._http.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            raise GoogleOAuthError(f"User info fetch failed: {resp.status_code}")
        return cast(dict[str, Any], resp.json())

    async def get_valid_token(self, account: GoogleAccount) -> str:
        skew_deadline = datetime.now(UTC) + timedelta(seconds=_TOKEN_EXPIRY_SKEW_SECONDS)
        if account.token_expiry and account.token_expiry > skew_deadline:
            return self._decrypt(account.access_token_encrypted)

        if not account.refresh_token_encrypted:
            # Access may still be usable for a few seconds; prefer fail-closed on missing refresh.
            if account.token_expiry and account.token_expiry > datetime.now(UTC):
                return self._decrypt(account.access_token_encrypted)
            raise GoogleTokenRefreshError("No refresh token available")

        refresh_token = self._decrypt(account.refresh_token_encrypted)
        new_tokens = await self._refresh_access_token(refresh_token)

        access_enc = self._encrypt(new_tokens["access_token"])
        refresh_enc = (
            self._encrypt(new_tokens["refresh_token"]) if new_tokens.get("refresh_token") else None
        )
        expiry = datetime.now(UTC) + timedelta(seconds=new_tokens.get("expires_in", 3600))

        await self.repo.update_tokens(
            account.id, access_enc, refresh_enc, expiry, tenant_id=self.tenant_id
        )
        await self.db.commit()
        account.access_token_encrypted = access_enc
        if refresh_enc is not None:
            account.refresh_token_encrypted = refresh_enc
        account.token_expiry = expiry

        return cast(str, new_tokens["access_token"])

    async def _refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        data = {
            "client_id": settings.sso_google_client_id,
            "client_secret": settings.sso_google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        last_status = 0
        for attempt in range(3):
            resp = await self._http.post(GOOGLE_TOKEN_URL, data=data)
            last_status = resp.status_code
            if resp.status_code == 200:
                return cast(dict[str, Any], resp.json())
            # Retry transient Google / network-edge failures only.
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                logger.warning(
                    "google_token_refresh.retry",
                    extra={"status": resp.status_code, "attempt": attempt + 1},
                )
                continue
            break
        logger.error("google_token_refresh.failed", extra={"status": last_status})
        raise GoogleTokenRefreshError(f"Token refresh failed: {last_status}")

    async def get_status(self) -> tuple[bool, GoogleAccount | None]:
        account = await self.repo.get_by_user(self.tenant_id, self.user_id)
        if not account:
            return False, None

        return True, account

    async def disconnect(self) -> bool:
        account = await self.repo.get_by_user(self.tenant_id, self.user_id)
        if not account:
            return False
        return await self.repo.deactivate(account.id, self.tenant_id)
