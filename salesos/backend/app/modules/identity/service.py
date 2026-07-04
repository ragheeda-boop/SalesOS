import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError, UnauthorizedError
from app.config import settings
from sdk.audit import AuditTrail
from sdk.events import EventBus
from sdk.events.domain_events import (
    TenantCreated,
    UserLoggedIn,
    UserPasswordChanged,
    UserRegistered,
    UserRoleChanged,
)
from sdk.telemetry import StructuredLogger

from .models import Tenant, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, tenant_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": secrets.token_urlsafe(16),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "iss": "salesos",
        "aud": "salesos-api",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": secrets.token_urlsafe(16),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "iss": "salesos",
        "aud": "salesos-api",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm],
            audience="salesos-api",
        )
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")
        return payload
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm],
            audience="salesos-api",
        )
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        return payload
    except JWTError:
        raise UnauthorizedError("Invalid or expired refresh token")


RESET_TOKEN_STORE: dict[str, dict] = {}


class IdentityService:
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.db = db
        self.event_bus = event_bus
        self.logger = logger

    async def create_tenant(self, name: str, slug: str, domain: str | None = None) -> Tenant:
        existing = await self.db.execute(select(Tenant).where(Tenant.slug == slug))
        if existing.scalar_one_or_none():
            raise DuplicateError("Tenant", "slug", slug)

        tenant = Tenant(name=name, slug=slug, domain=domain)
        self.db.add(tenant)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(tenant.id),
            entity_type="tenant",
            entity_id=str(tenant.id),
            action="created",
        )
        if self.event_bus:
            await self.event_bus.publish(
                TenantCreated(
                    tenant_id=str(tenant.id),
                    aggregate_id=str(tenant.id),
                    aggregate_type="tenant",
                    data={"name": name, "slug": slug, "domain": domain},
                )
            )

        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError("Tenant", tenant_id)
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        result = await self.db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        full_name_ar: str | None = None,
        tenant_id: str | None = None,
    ) -> User:
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise DuplicateError("User", "email", email)

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            full_name_ar=full_name_ar,
            tenant_id=tenant_id,
        )
        self.db.add(user)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=str(user.tenant_id) if user.tenant_id else "",
            entity_type="user",
            entity_id=str(user.id),
            action="created",
        )
        if self.event_bus:
            await self.event_bus.publish(
                UserRegistered(
                    tenant_id=str(user.tenant_id) if user.tenant_id else "",
                    aggregate_id=str(user.id),
                    aggregate_type="user",
                    data={"email": email, "full_name": full_name},
                )
            )

        return user

    async def authenticate(self, email: str, password: str) -> User:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        if self.event_bus:
            await self.event_bus.publish(
                UserLoggedIn(
                    tenant_id=str(user.tenant_id) if user.tenant_id else "",
                    aggregate_id=str(user.id),
                    aggregate_type="user",
                    data={"email": email},
                )
            )

        return user

    async def get_user(self, user_id: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def get_users_by_tenant(self, tenant_id: str) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
        )
        return list(result.scalars().all())

    async def update_user_role(self, user_id: str, role: str) -> User:
        user = await self.get_user(user_id)
        old_role = user.role
        user.role = role
        await self.db.flush()

        if self.event_bus:
            await self.event_bus.publish(
                UserRoleChanged(
                    tenant_id=str(user.tenant_id) if user.tenant_id else "",
                    aggregate_id=str(user.id),
                    aggregate_type="user",
                    data={"old_role": old_role, "new_role": role},
                )
            )

        return user

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> User:
        user = await self.get_user(user_id)
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect")
        user.password_hash = hash_password(new_password)
        await self.db.flush()

        if self.event_bus:
            await self.event_bus.publish(
                UserPasswordChanged(
                    tenant_id=str(user.tenant_id) if user.tenant_id else "",
                    aggregate_id=str(user.id),
                    aggregate_type="user",
                )
            )

        return user

    async def forgot_password(self, email: str) -> str:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return "sent"
        token = secrets.token_urlsafe(32)
        RESET_TOKEN_STORE[token] = {
            "user_id": str(user.id),
            "expires": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        if self.logger:
            self.logger.info("Password reset token generated for user=%s", email)
        return token

    async def reset_password(self, token: str, new_password: str) -> User:
        data = RESET_TOKEN_STORE.pop(token, None)
        if not data:
            raise UnauthorizedError("Invalid or expired reset token")
        if datetime.now(timezone.utc) > data["expires"]:
            raise UnauthorizedError("Reset token has expired")
        user = await self.get_user(data["user_id"])
        user.password_hash = hash_password(new_password)
        await self.db.flush()
        return user
