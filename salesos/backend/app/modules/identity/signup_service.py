import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError
from app.modules.identity.models import Tenant, User
from app.modules.identity.repositories import TenantRepository, UserRepository
from app.modules.identity.service import _publish_best_effort, hash_password
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
        tenant_repo: TenantRepository | None = None,
        user_repo: UserRepository | None = None,
        event_bus: EventBus | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.db = db
        self._tenant_repo = tenant_repo or TenantRepository(db)
        self._user_repo = user_repo or UserRepository(db)
        self.event_bus = event_bus
        self.logger = logger

    async def signup(
        self,
        email: str,
        password: str,
        company_name: str,
        phone: str | None = None,
    ) -> dict[str, Any]:
        if await self._user_repo.exists_by_email(email):
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
            "expires_at": datetime.now(UTC) + timedelta(hours=24),
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

        await _publish_best_effort(
            self.event_bus,
            TenantCreated(
                tenant_id=str(tenant.id),
                aggregate_id=str(tenant.id),
                aggregate_type="tenant",
                data={"name": company_name, "slug": slug},
            ),
            logger=self.logger,
            entity_type="tenant",
            aggregate_id=str(tenant.id),
        )
        await _publish_best_effort(
            self.event_bus,
            UserRegistered(
                tenant_id=str(tenant.id),
                aggregate_id=str(user.id),
                aggregate_type="user",
                data={"email": email},
            ),
            logger=self.logger,
            entity_type="user",
            aggregate_id=str(user.id),
        )

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
        if data["expires_at"] < datetime.now(UTC):
            del VERIFICATION_TOKENS[token]
            raise ValueError("Verification token expired")

        try:
            user = await self._user_repo.get(uuid.UUID(data["user_id"]))
        except Exception:
            del VERIFICATION_TOKENS[token]
            raise ValueError("User not found") from None

        user.is_verified = True
        await self.db.flush()
        del VERIFICATION_TOKENS[token]
        return {"message": "Email verified successfully", "user_id": str(user.id)}

    async def resend_verification(self, email: str) -> dict[str, Any]:
        user = await self._user_repo.get_by_email(email)
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
            "expires_at": datetime.now(UTC) + timedelta(hours=24),
        }
        return {
            "message": "Verification email resent",
            "verification_token": new_token,
        }
