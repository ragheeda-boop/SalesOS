import uuid
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.modules.identity.models import Tenant, User
from app.modules.identity.service import IdentityService, hash_password
from sdk.audit import AuditTrail
from sdk.events import EventBus
from sdk.events.domain_events import UserInvited
from sdk.telemetry import StructuredLogger

logger = logging.getLogger(__name__)

INVITE_TOKENS: dict[str, dict[str, Any]] = {}


class InviteService:
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.db = db
        self.event_bus = event_bus
        self.logger = logger

    async def create_invite(
        self,
        email: str,
        role: str,
        invited_by: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        existing_user = await self.db.execute(select(User).where(User.email == email))
        if existing_user.scalar_one_or_none():
            raise DuplicateError("User", "email", email)

        token = secrets.token_urlsafe(32)
        INVITE_TOKENS[token] = {
            "email": email,
            "role": role,
            "tenant_id": tenant_id,
            "invited_by": invited_by,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "accepted": False,
        }

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=tenant_id,
            entity_type="user_invite",
            entity_id=email,
            action="invited",
            details={"invited_by": invited_by, "role": role},
        )

        if self.event_bus:
            try:
                await self.event_bus.publish(
                    UserInvited(
                        tenant_id=tenant_id,
                        aggregate_id=email,
                        aggregate_type="user_invite",
                        data={"email": email, "role": role, "invited_by": invited_by},
                    )
                )
            except Exception as e:
                if self.logger:
                    self.logger.warn("event.publish_failed", error=str(e))

        return {
            "email": email,
            "role": role,
            "invite_token": token,
            "expires_at": INVITE_TOKENS[token]["expires_at"],
        }

    async def validate_invite(self, token: str) -> dict[str, Any]:
        data = INVITE_TOKENS.get(token)
        if not data:
            raise ValueError("Invalid invite token")
        if data["accepted"]:
            raise ValueError("Invite has already been accepted")
        if data["expires_at"] < datetime.now(timezone.utc):
            del INVITE_TOKENS[token]
            raise ValueError("Invite token has expired")
        return {
            "email": data["email"],
            "tenant_id": data["tenant_id"],
            "role": data["role"],
        }

    async def accept_invite(self, token: str, password: str, full_name: str) -> dict[str, Any]:
        data = INVITE_TOKENS.get(token)
        if not data:
            raise ValueError("Invalid invite token")
        if data["accepted"]:
            raise ValueError("Invite has already been accepted")
        if data["expires_at"] < datetime.now(timezone.utc):
            del INVITE_TOKENS[token]
            raise ValueError("Invite token has expired")

        existing = await self.db.execute(select(User).where(User.email == data["email"]))
        if existing.scalar_one_or_none():
            raise DuplicateError("User", "email", data["email"])

        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == data["tenant_id"])
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError("Tenant", data["tenant_id"])

        user = User(
            email=data["email"],
            password_hash=hash_password(password),
            full_name=full_name,
            tenant_id=tenant.id,
            is_verified=True,
            role=data["role"],
        )
        self.db.add(user)
        await self.db.flush()

        data["accepted"] = True

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(tenant.id),
            entity_type="user",
            entity_id=str(user.id),
            action="invite_accepted",
            details={"email": data["email"]},
        )

        return {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "email": data["email"],
            "role": data["role"],
        }
