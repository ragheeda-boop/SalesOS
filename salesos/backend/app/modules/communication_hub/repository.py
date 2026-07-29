"""Repository for Google Accounts — Communication Hub."""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication_hub.models import GoogleAccount

logger = logging.getLogger(__name__)


class GoogleAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user(
        self, tenant_id: UUID, user_id: UUID
    ) -> GoogleAccount | None:
        stmt = (
            select(GoogleAccount)
            .where(
                GoogleAccount.tenant_id == tenant_id,
                GoogleAccount.user_id == user_id,
                GoogleAccount.is_active.is_(True),
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self, *, limit: int = 500) -> list[GoogleAccount]:
        """All active Google accounts (periodic background sync)."""
        stmt = (
            select(GoogleAccount)
            .where(GoogleAccount.is_active.is_(True))
            .limit(max(1, min(limit, 2000)))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self, account_id: UUID, tenant_id: UUID
    ) -> GoogleAccount | None:
        stmt = (
            select(GoogleAccount)
            .where(
                GoogleAccount.id == account_id,
                GoogleAccount.tenant_id == tenant_id,
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: UUID,
        user_id: UUID,
        email: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        token_expiry: datetime | None,
        scope: str | None = None,
        google_user_id: str | None = None,
        avatar_url: str | None = None,
    ) -> GoogleAccount:
        account = GoogleAccount(
            tenant_id=tenant_id,
            user_id=user_id,
            email=email,
            provider="google",
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            token_expiry=token_expiry,
            scope=scope,
            google_user_id=google_user_id,
            avatar_url=avatar_url,
        )
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        logger.info("google_account.created", extra={"tenant_id": str(tenant_id), "email": email})
        return account

    async def update_tokens(
        self,
        account_id: UUID,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        token_expiry: datetime | None,
        tenant_id: UUID,
    ) -> None:
        """Update tokens — tenant_id is required (cross-tenant IDOR prevention)."""
        values: dict = {
            "access_token_encrypted": access_token_encrypted,
            "updated_at": datetime.now(timezone.utc),
        }
        if refresh_token_encrypted is not None:
            values["refresh_token_encrypted"] = refresh_token_encrypted
        if token_expiry is not None:
            values["token_expiry"] = token_expiry

        stmt = (
            update(GoogleAccount)
            .where(
                GoogleAccount.id == account_id,
                GoogleAccount.tenant_id == tenant_id,
            )
            .values(**values)
        )
        await self.db.execute(stmt)

    async def update_last_sync(self, account_id: UUID, tenant_id: UUID) -> None:
        stmt = (
            update(GoogleAccount)
            .where(
                GoogleAccount.id == account_id,
                GoogleAccount.tenant_id == tenant_id,
            )
            .values(last_sync_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)

    async def update_history_id(
        self, account_id: UUID, history_id: str | None, tenant_id: UUID
    ) -> None:
        stmt = (
            update(GoogleAccount)
            .where(
                GoogleAccount.id == account_id,
                GoogleAccount.tenant_id == tenant_id,
            )
            .values(history_id=history_id, updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)

    async def update_calendar_sync_token(
        self,
        account_id: UUID,
        sync_token: str | None,
        tenant_id: UUID,
    ) -> None:
        stmt = (
            update(GoogleAccount)
            .where(
                GoogleAccount.id == account_id,
                GoogleAccount.tenant_id == tenant_id,
            )
            .values(
                calendar_sync_token=sync_token,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt)

    async def deactivate(self, account_id: UUID, tenant_id: UUID) -> bool:
        stmt = (
            update(GoogleAccount)
            .where(
                GoogleAccount.id == account_id,
                GoogleAccount.tenant_id == tenant_id,
            )
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
