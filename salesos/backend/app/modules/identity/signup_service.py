import uuid
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError
from app.config import settings
from app.modules.identity.models import Tenant, User
from app.modules.identity.service import IdentityService, hash_password
from sdk.audit import AuditTrail
from sdk.events import EventBus
from sdk.events.domain_events import TenantCreated, UserRegistered
from sdk.telemetry import StructuredLogger

logger = logging.getLogger(__name__)

VERIFICATION_TOKENS: dict[str, dict[str, Any]] = {}


def _generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


class SignupService:
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.db = db
        self.event_bus = event_bus
        self.logger = logger

    async def signup(
        self,
        email: str,
        password: str,
        company_name: str,
        phone: str | None = None,
    ) -> dict[str, Any]:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise DuplicateError("User", "email", email)

        slug = secrets.token_urlsafe(8).lower()
        tenant = Tenant(
            name=company_name,
            slug=slug,
            plan="free",
        )
        self.db.add(tenant)
        await self.db.flush()

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=company_name,
            tenant_id=tenant.id,
            is_verified=False,
            phone=phone,
            role="admin",
        )
        self.db.add(user)
        await self.db.flush()

        token = _generate_verification_token()
        VERIFICATION_TOKENS[token] = {
            "user_id": str(user.id),
            "email": email,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
        }

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(tenant.id),
            entity_type="tenant",
            entity_id=str(tenant.id),
            action="created",
        )
        await audit.record(
            tenant_id=str(tenant.id),
            entity_type="user",
            entity_id=str(user.id),
            action="created",
        )

        if self.event_bus:
            try:
                await self.event_bus.publish(
                    TenantCreated(
                        tenant_id=str(tenant.id),
                        aggregate_id=str(tenant.id),
                        aggregate_type="tenant",
                        data={"name": company_name, "slug": slug},
                    )
                )
                await self.event_bus.publish(
                    UserRegistered(
                        tenant_id=str(tenant.id),
                        aggregate_id=str(user.id),
                        aggregate_type="user",
                        data={"email": email},
                    )
                )
            except Exception as e:
                if self.logger:
                    self.logger.warn("event.publish_failed", error=str(e))

        return {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "verification_token": token,
            "email": email,
        }

    async def verify_email(self, token: str) -> dict[str, Any]:
        data = VERIFICATION_TOKENS.get(token)
        if not data:
            raise ValueError("Invalid verification token")
        if data["expires_at"] < datetime.now(timezone.utc):
            del VERIFICATION_TOKENS[token]
            raise ValueError("Verification token expired")

        result = await self.db.execute(
            select(User).where(User.id == data["user_id"])
        )
        user = result.scalar_one_or_none()
        if not user:
            del VERIFICATION_TOKENS[token]
            raise ValueError("User not found")

        user.is_verified = True
        await self.db.flush()
        del VERIFICATION_TOKENS[token]
        return {"message": "Email verified successfully", "user_id": str(user.id)}

    async def resend_verification(self, email: str) -> dict[str, Any]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return {"message": "If the email exists, a verification link has been sent"}
        if user.is_verified:
            return {"message": "Email is already verified"}

        for token_key, token_data in list(VERIFICATION_TOKENS.items()):
            if token_data["email"] == email:
                del VERIFICATION_TOKENS[token_key]

        new_token = _generate_verification_token()
        VERIFICATION_TOKENS[new_token] = {
            "user_id": str(user.id),
            "email": email,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
        }
        return {
            "message": "Verification email resent",
            "verification_token": new_token,
        }
