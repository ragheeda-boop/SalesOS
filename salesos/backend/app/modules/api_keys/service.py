from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError, UnauthorizedError
from app.config import settings

from .models import ApiKey

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_key(raw_key: str) -> str:
    return pwd_context.hash(raw_key)


def _verify_key(raw_key: str, key_hash: str) -> bool:
    return pwd_context.verify(raw_key, key_hash)


def _generate_api_key() -> tuple[str, str, str]:
    raw = secrets.token_hex(32)
    key = f"sos_{raw}"
    prefix = key[:10]
    return key, prefix, _hash_key(key)


class ApiKeyService:
    def __init__(self, db: AsyncSession, logger: Any = None):
        self.db = db
        self.logger = logger

    async def create(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        permissions: dict[str, Any] | None = None,
        scopes: list[str] | None = None,
        expiry_days: int | None = None,
    ) -> tuple[ApiKey, str]:
        raw_key, prefix, key_hash = _generate_api_key()
        expires_at = None
        if expiry_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days)
        if not expiry_days and settings.api_key_expiry_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.api_key_expiry_days)

        api_key = ApiKey(
            id=secrets.token_urlsafe(16),
            tenant_id=uuid.UUID(tenant_id),
            user_id=uuid.UUID(user_id),
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            permissions=permissions or {},
            scopes=",".join(scopes) if scopes else None,
            expires_at=expires_at,
        )
        self.db.add(api_key)
        await self.db.flush()
        return api_key, raw_key

    async def validate(self, key: str) -> ApiKey | None:
        prefix = key[:10]
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.key_prefix == prefix,
                ApiKey.is_revoked.is_(False),
            )
        )
        keys = list(result.scalars().all())
        for api_key in keys:
            if _verify_key(key, api_key.key_hash):
                if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                    api_key.is_revoked = True
                    await self.db.flush()
                    return None
                api_key.last_used_at = datetime.now(timezone.utc)
                await self.db.flush()
                return api_key
        return None

    async def revoke(self, key_id: str, user_id: str) -> bool:
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == uuid.UUID(user_id),
                ApiKey.is_revoked.is_(False),
            )
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            return False
        api_key.is_revoked = True
        api_key.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.user_id == uuid.UUID(user_id),
                ApiKey.is_revoked.is_(False),
            ).order_by(ApiKey.created_at.desc())
        )
        keys = list(result.scalars().all())
        return [
            {
                "id": k.id,
                "name": k.name,
                "key_prefix": k.key_prefix + "..." + k.id[-4:],
                "scopes": k.scopes.split(",") if k.scopes else [],
                "permissions": k.permissions,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "created_at": k.created_at.isoformat() if k.created_at else None,
            }
            for k in keys
        ]

    async def get_by_id(self, key_id: str) -> ApiKey:
        result = await self.db.execute(select(ApiKey).where(ApiKey.id == key_id))
        key = result.scalar_one_or_none()
        if not key:
            raise NotFoundError("ApiKey", key_id)
        return key
