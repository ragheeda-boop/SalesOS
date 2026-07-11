import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import UnauthorizedError
from app.config import settings
from app.modules.identity.models import User
from app.modules.identity.service import (
    IdentityService,
    create_access_token,
    hash_password,
)

from .models import SSOConnection

PROVIDER_CONFIGS: dict[str, dict[str, Any]] = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "client_id": lambda: settings.sso_google_client_id,
        "client_secret": lambda: settings.sso_google_client_secret,
        "scopes": ["openid", "email", "profile"],
    },
    "microsoft": {
        "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "client_id": lambda: settings.sso_microsoft_client_id,
        "client_secret": lambda: settings.sso_microsoft_client_secret,
        "scopes": ["User.Read", "email", "openid", "profile"],
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "client_id": lambda: settings.sso_github_client_id,
        "client_secret": lambda: settings.sso_github_client_secret,
        "scopes": ["read:user", "user:email"],
    },
}


class OAuthService:
    def __init__(self, db: AsyncSession, logger: Any = None):
        self.db = db
        self.logger = logger

    def _get_provider_config(self, provider: str) -> dict[str, Any]:
        config = PROVIDER_CONFIGS.get(provider)
        if not config:
            raise ValueError(f"Unsupported provider: {provider}")
        return config

    def _base_redirect_uri(self, provider: str) -> str:
        base = settings.next_public_api_url.rstrip("/")
        return f"{base}/api/v1/auth/sso/{provider}/callback"

    def get_authorization_url(self, provider: str) -> str:
        config = self._get_provider_config(provider)
        state = secrets.token_urlsafe(32)
        params = {
            "client_id": config["client_id"](),
            "redirect_uri": self._base_redirect_uri(provider),
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        from urllib.parse import urlencode
        return f"{config['authorize_url']}?{urlencode(params)}"

    async def handle_callback(self, provider: str, code: str, state: str) -> tuple[str, str]:
        config = self._get_provider_config(provider)
        token_data = await self._exchange_code(provider, config, code)
        user_info = await self._fetch_user_info(provider, config, token_data["access_token"])
        provider_user_id = str(user_info.get("id", ""))
        email = user_info.get("email", "")
        if not email:
            if provider == "github":
                emails = await self._fetch_github_emails(token_data["access_token"])
                email = emails[0]["email"] if emails else ""
            if not email:
                raise UnauthorizedError(f"Could not retrieve email from {provider}")

        result = await self.db.execute(
            select(SSOConnection).where(
                SSOConnection.provider == provider,
                SSOConnection.provider_user_id == provider_user_id,
                SSOConnection.is_active.is_(True),
            )
        )
        connection = result.scalar_one_or_none()

        if connection:
            user_result = await self.db.execute(select(User).where(User.id == connection.user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                raise UnauthorizedError("Linked user not found")
            connection.access_token = token_data["access_token"]
            connection.refresh_token = token_data.get("refresh_token", connection.refresh_token)
            if "expires_in" in token_data:
                connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
            await self.db.flush()
        else:
            user_result = await self.db.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()
            if not user:
                from app.modules.identity.models import Tenant
                tenant_name = email.split("@")[0]
                tenant = Tenant(
                    id=uuid.uuid4(),
                    name=tenant_name,
                    slug=secrets.token_urlsafe(8).lower(),
                    plan="free",
                )
                self.db.add(tenant)
                await self.db.flush()
                user = User(
                    email=email,
                    password_hash=hash_password(secrets.token_urlsafe(32)),
                    full_name=user_info.get("name", tenant_name),
                    tenant_id=tenant.id,
                    is_verified=True,
                )
                self.db.add(user)
                await self.db.flush()
            connection = SSOConnection(
                id=secrets.token_urlsafe(16),
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=email,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600)) if "expires_in" in token_data else None,
            )
            self.db.add(connection)
            await self.db.flush()

        access_token = create_access_token(str(user.id), str(user.tenant_id))
        return access_token, str(user.id)

    async def _exchange_code(self, provider: str, config: dict[str, Any], code: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            headers = {"Accept": "application/json"}
            if provider == "github":
                headers["Accept"] = "application/json"
            resp = await client.post(
                config["token_url"],
                data={
                    "client_id": config["client_id"](),
                    "client_secret": config["client_secret"](),
                    "code": code,
                    "redirect_uri": self._base_redirect_uri(provider),
                    "grant_type": "authorization_code",
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise UnauthorizedError(f"OAuth token exchange failed: {data.get('error_description', data['error'])}")
            return data

    async def _fetch_user_info(self, provider: str, config: dict[str, Any], access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            if provider == "github":
                headers["Accept"] = "application/vnd.github+json"
            resp = await client.get(config["userinfo_url"], headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def _fetch_github_emails(self, access_token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_connections_for_user(self, user_id: str) -> list[SSOConnection]:
        result = await self.db.execute(
            select(SSOConnection).where(
                SSOConnection.user_id == uuid.UUID(user_id),
                SSOConnection.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def disconnect_provider(self, user_id: str, provider: str) -> bool:
        result = await self.db.execute(
            select(SSOConnection).where(
                SSOConnection.user_id == uuid.UUID(user_id),
                SSOConnection.provider == provider,
                SSOConnection.is_active.is_(True),
            )
        )
        connection = result.scalar_one_or_none()
        if not connection:
            return False
        connection.is_active = False
        await self.db.flush()
        return True
