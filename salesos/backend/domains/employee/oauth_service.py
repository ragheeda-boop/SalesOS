"""Employee OAuth token management — encrypted storage, rotation, lifecycle.

Supports: Google Workspace (Gmail + Calendar), Microsoft 365 (Outlook + Calendar).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models import Base


class EmployeeOAuthToken(Base):
    """Encrypted OAuth tokens per employee per provider."""

    __tablename__ = "employee_oauth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(20), nullable=False)  # google, microsoft
    scope = Column(String(500), nullable=True)  # granted scopes

    # Token data (encrypted at rest — use Fernet or KMS)
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    id_token_encrypted = Column(Text, nullable=True)

    # Token lifecycle
    access_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Sync state
    calendar_sync_token = Column(String(500), nullable=True)    # Google syncToken
    calendar_delta_link = Column(String(1000), nullable=True)   # MS Graph deltaLink
    email_history_id = Column(String(500), nullable=True)        # Gmail historyId
    email_delta_link = Column(String(1000), nullable=True)      # MS Graph deltaLink
    last_calendar_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_email_sync_at = Column(DateTime(timezone=True), nullable=True)

    # Webhook
    webhook_channel_id = Column(String(255), nullable=True)
    webhook_resource_id = Column(String(255), nullable=True)
    webhook_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    connection_error = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    max_failures = Column(Integer, default=10)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_oauth_tokens_employee_provider", "employee_id", "provider", unique=True),
        Index("ix_oauth_tokens_tenant", "tenant_id"),
        Index("ix_oauth_tokens_expires", "access_token_expires_at"),
        Index("ix_oauth_tokens_webhook_channel", "webhook_channel_id"),
    )

    def is_access_token_expired(self) -> bool:
        if not self.access_token_expires_at:
            return True
        return self.access_token_expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5)

    def is_refresh_token_expired(self) -> bool:
        if not self.refresh_token_expires_at:
            return False
        return self.refresh_token_expires_at <= datetime.now(timezone.utc)

    def should_retry(self) -> bool:
        if not self.is_active:
            return False
        return self.consecutive_failures < self.max_failures

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.connection_error = None
        self.is_connected = True
        self.last_used_at = datetime.now(timezone.utc)

    def record_failure(self, error: str) -> None:
        self.consecutive_failures += 1
        self.connection_error = error
        self.last_used_at = datetime.now(timezone.utc)
        if self.consecutive_failures >= self.max_failures:
            self.is_connected = False


class OAuthTokenService:
    """Manages OAuth token lifecycle: storage, encryption, refresh, rotation."""

    def __init__(
        self,
        db: AsyncSession,
        encryption_key: bytes | None = None,
        google_client_id: str = "",
        google_client_secret: str = "",
        microsoft_client_id: str = "",
        microsoft_client_secret: str = "",
    ):
        self.db = db
        self._encryption_key = encryption_key
        self._google_client_id = google_client_id
        self._google_client_secret = google_client_secret
        self._microsoft_client_id = microsoft_client_id
        self._microsoft_client_secret = microsoft_client_secret

    async def store_tokens(
        self,
        employee_id: str,
        tenant_id: str,
        provider: str,
        access_token: str,
        refresh_token: str | None,
        id_token: str | None,
        expires_in: int,
        scope: str,
    ) -> EmployeeOAuthToken:
        now = datetime.now(timezone.utc)
        token = EmployeeOAuthToken(
            employee_id=uuid.UUID(employee_id),
            tenant_id=uuid.UUID(tenant_id),
            provider=provider,
            scope=scope,
            access_token_encrypted=await self._encrypt(access_token) if access_token else None,
            refresh_token_encrypted=await self._encrypt(refresh_token) if refresh_token else None,
            id_token_encrypted=await self._encrypt(id_token) if id_token else None,
            access_token_expires_at=now + timedelta(seconds=expires_in),
            refresh_token_expires_at=None,
            last_refreshed_at=now,
            last_used_at=now,
            is_active=True,
            is_connected=True,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_access_token(self, employee_id: str, provider: str) -> str | None:
        token = await self._get_token(employee_id, provider)
        if not token or not token.access_token_encrypted:
            return None
        return await self._decrypt(token.access_token_encrypted)

    async def get_refresh_token(self, employee_id: str, provider: str) -> str | None:
        token = await self._get_token(employee_id, provider)
        if not token or not token.refresh_token_encrypted:
            return None
        return await self._decrypt(token.refresh_token_encrypted)

    async def update_access_token(
        self, employee_id: str, provider: str,
        access_token: str, expires_in: int,
    ) -> None:
        token = await self._get_token(employee_id, provider)
        if token:
            token.access_token_encrypted = await self._encrypt(access_token)
            token.access_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            token.last_refreshed_at = datetime.now(timezone.utc)
            token.record_success()
            await self.db.flush()

    async def update_sync_token(
        self, employee_id: str, provider: str,
        sync_type: str, sync_value: str,
    ) -> None:
        token = await self._get_token(employee_id, provider)
        if not token:
            return
        if sync_type == "calendar":
            if provider == "google":
                token.calendar_sync_token = sync_value
            else:
                token.calendar_delta_link = sync_value
            token.last_calendar_sync_at = datetime.now(timezone.utc)
        elif sync_type == "email":
            if provider == "google":
                token.email_history_id = sync_value
            else:
                token.email_delta_link = sync_value
            token.last_email_sync_at = datetime.now(timezone.utc)
        token.record_success()
        await self.db.flush()

    async def store_webhook_channel(
        self, employee_id: str, provider: str,
        channel_id: str, resource_id: str, expires_at: datetime,
    ) -> None:
        token = await self._get_token(employee_id, provider)
        if token:
            token.webhook_channel_id = channel_id
            token.webhook_resource_id = resource_id
            token.webhook_expires_at = expires_at
            await self.db.flush()

    async def invalidate(self, employee_id: str, provider: str) -> None:
        token = await self._get_token(employee_id, provider)
        if token:
            token.is_active = False
            token.is_connected = False
            token.access_token_encrypted = None
            token.refresh_token_encrypted = None
            await self.db.flush()

    async def _get_token(self, employee_id: str, provider: str) -> EmployeeOAuthToken | None:
        from sqlalchemy import select
        result = await self.db.execute(
            select(EmployeeOAuthToken).where(
                EmployeeOAuthToken.employee_id == uuid.UUID(employee_id),
                EmployeeOAuthToken.provider == provider,
                EmployeeOAuthToken.is_active == True,
            ).order_by(EmployeeOAuthToken.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _encrypt(self, value: str) -> str:
        if not self._encryption_key:
            from cryptography.fernet import Fernet
            import base64, hashlib
            key = base64.urlsafe_b64encode(hashlib.sha256(b"salesos_employee_oauth_v1").digest())
            cipher = Fernet(key)
        else:
            from cryptography.fernet import Fernet
            cipher = Fernet(self._encryption_key)
        return cipher.encrypt(value.encode()).decode()

    async def _decrypt(self, encrypted: str) -> str:
        if not self._encryption_key:
            from cryptography.fernet import Fernet
            import base64, hashlib
            key = base64.urlsafe_b64encode(hashlib.sha256(b"salesos_employee_oauth_v1").digest())
            cipher = Fernet(key)
        else:
            from cryptography.fernet import Fernet
            cipher = Fernet(self._encryption_key)
        return cipher.decrypt(encrypted.encode()).decode()
