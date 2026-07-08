import uuid
import hashlib
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

from .models import DeviceSession, PasswordResetToken, RefreshTokenFamily, Tenant, TokenBlacklist, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_id() -> str:
    return secrets.token_urlsafe(16)


def create_access_token(user_id: str, tenant_id: str, jti: str | None = None) -> str:
    expire = _now() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": jti or secrets.token_urlsafe(16),
        "exp": expire,
        "iat": _now(),
        "type": "access",
        "iss": "salesos",
        "aud": "salesos-api",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, tenant_id: str, jti: str | None = None) -> str:
    expire = _now() + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": jti or secrets.token_urlsafe(16),
        "exp": expire,
        "iat": _now(),
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

    # ── Refresh Token Family Management ──────────────────────────────────

    async def create_token_family(
        self, user_id: str, tenant_id: str,
    ) -> tuple[str, str, str, str]:
        family_id = _generate_id()
        jti = secrets.token_urlsafe(16)
        refresh_token = create_refresh_token(user_id, tenant_id, jti=jti)
        token_hash = _hash_jti(jti)
        family = RefreshTokenFamily(
            id=_generate_id(),
            user_id=uuid.UUID(user_id),
            family_id=family_id,
            token_hash=token_hash,
            expires_at=_now() + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
        self.db.add(family)
        await self.db.flush()
        return refresh_token, family_id, family.id, jti

    async def rotate_refresh_token(
        self, refresh_token_jti: str, user_id: str, tenant_id: str,
    ) -> tuple[str, str]:
        token_hash = _hash_jti(refresh_token_jti)
        result = await self.db.execute(
            select(RefreshTokenFamily).where(
                RefreshTokenFamily.token_hash == token_hash,
                RefreshTokenFamily.is_compromised.is_(False),
            )
        )
        family = result.scalar_one_or_none()
        if not family:
            raise UnauthorizedError("Invalid or expired refresh token")
        if family.used_at is not None:
            family.is_compromised = True
            await self.db.flush()
            await self._revoke_family_sessions(family.family_id)
            if self.logger:
                self.logger.warn(
                    "refresh.reuse_detected",
                    user_id=user_id,
                    family_id=family.family_id,
                )
            raise UnauthorizedError("Refresh token reuse detected — session revoked")
        if family.expires_at < _now():
            raise UnauthorizedError("Refresh token expired")
        family.used_at = _now()
        new_jti = secrets.token_urlsafe(16)
        new_refresh = create_refresh_token(user_id, tenant_id, jti=new_jti)
        new_family = RefreshTokenFamily(
            id=_generate_id(),
            user_id=uuid.UUID(user_id),
            family_id=family.family_id,
            token_hash=_hash_jti(new_jti),
            expires_at=_now() + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
        self.db.add(new_family)
        new_access = create_access_token(user_id, tenant_id)
        await self.db.flush()
        return new_access, new_refresh

    async def _revoke_family_sessions(self, family_id: str) -> None:
        result = await self.db.execute(
            select(DeviceSession).where(
                DeviceSession.refresh_family_id == family_id,
                DeviceSession.is_revoked.is_(False),
            )
        )
        sessions = list(result.scalars().all())
        for s in sessions:
            s.is_revoked = True
        await self.db.flush()

    # ── Device Session Management ────────────────────────────────────────

    async def create_device_session(
        self,
        user_id: str,
        tenant_id: str,
        refresh_family_id: str,
        device_name: str = "",
        device_type: str = "unknown",
        ip_address: str = "",
    ) -> DeviceSession:
        session = DeviceSession(
            id=_generate_id(),
            user_id=uuid.UUID(user_id),
            tenant_id=uuid.UUID(tenant_id),
            refresh_family_id=refresh_family_id,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            expires_at=_now() + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_user_sessions(self, user_id: str) -> list[DeviceSession]:
        result = await self.db.execute(
            select(DeviceSession).where(
                DeviceSession.user_id == user_id,
                DeviceSession.is_revoked.is_(False),
                DeviceSession.expires_at > _now(),
            ).order_by(DeviceSession.last_used_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_session(self, session_id: str, user_id: str) -> int:
        result = await self.db.execute(
            select(DeviceSession).where(
                DeviceSession.id == session_id,
                DeviceSession.user_id == user_id,
                DeviceSession.is_revoked.is_(False),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return 0
        session.is_revoked = True
        await self._revoke_family_sessions(session.refresh_family_id)
        await self.db.flush()
        return 1

    async def revoke_all_user_sessions(self, user_id: str) -> int:
        result = await self.db.execute(
            select(DeviceSession).where(
                DeviceSession.user_id == user_id,
                DeviceSession.is_revoked.is_(False),
            )
        )
        sessions = list(result.scalars().all())
        family_ids = {s.refresh_family_id for s in sessions}
        for s in sessions:
            s.is_revoked = True
        result2 = await self.db.execute(
            select(RefreshTokenFamily).where(
                RefreshTokenFamily.family_id.in_(family_ids),
                RefreshTokenFamily.is_compromised.is_(False),
            )
        )
        families = list(result2.scalars().all())
        for f in families:
            f.is_compromised = True
        await self.db.flush()
        return len(sessions)

    # ── Token Blacklist ──────────────────────────────────────────────────

    async def blacklist_token(self, jti: str, token_type: str, expires_at: datetime) -> None:
        entry = TokenBlacklist(
            jti=jti,
            token_type=token_type,
            expires_at=expires_at,
        )
        self.db.add(entry)

    async def is_token_blacklisted(self, jti: str) -> bool:
        result = await self.db.execute(
            select(TokenBlacklist).where(
                TokenBlacklist.jti == jti,
                TokenBlacklist.expires_at > _now(),
            )
        )
        return result.scalar_one_or_none() is not None

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
            try:
                await self.event_bus.publish(
                    TenantCreated(
                        tenant_id=str(tenant.id),
                        aggregate_id=str(tenant.id),
                        aggregate_type="tenant",
                        data={"name": name, "slug": slug, "domain": domain},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="tenant", aggregate_id=str(tenant.id))

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
            try:
                await self.event_bus.publish(
                    UserRegistered(
                        tenant_id=str(user.tenant_id) if user.tenant_id else "",
                        aggregate_id=str(user.id),
                        aggregate_type="user",
                        data={"email": email, "full_name": full_name},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="user", aggregate_id=str(user.id))

        return user

    async def authenticate(self, email: str, password: str) -> User:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        if self.event_bus:
            try:
                await self.event_bus.publish(
                    UserLoggedIn(
                        tenant_id=str(user.tenant_id) if user.tenant_id else "",
                        aggregate_id=str(user.id),
                        aggregate_type="user",
                        data={"email": email},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="user", aggregate_id=str(user.id))

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
            try:
                await self.event_bus.publish(
                    UserRoleChanged(
                        tenant_id=str(user.tenant_id) if user.tenant_id else "",
                        aggregate_id=str(user.id),
                        aggregate_type="user",
                        data={"old_role": old_role, "new_role": role},
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="user", aggregate_id=str(user.id))

        return user

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> User:
        user = await self.get_user(user_id)
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect")
        user.password_hash = hash_password(new_password)
        await self.db.flush()

        if self.event_bus:
            try:
                await self.event_bus.publish(
                    UserPasswordChanged(
                        tenant_id=str(user.tenant_id) if user.tenant_id else "",
                        aggregate_id=str(user.id),
                        aggregate_type="user",
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn("event.publish_failed", entity_type="user", aggregate_id=str(user.id))

        return user

    async def forgot_password(self, email: str) -> None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            if self.logger:
                self.logger.info("Password reset requested for unknown email=%s", email)
            return
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        reset = PasswordResetToken(
            id=secrets.token_urlsafe(16),
            user_id=str(user.id),
            token_hash=token_hash,
            expires_at=now + timedelta(hours=1),
        )
        self.db.add(reset)
        await self.db.flush()
        if self.logger:
            self.logger.info("Password reset token generated for user=%s", email)

    async def reset_password(self, token: str, new_password: str) -> User:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
        reset = result.scalar_one_or_none()
        if not reset:
            raise UnauthorizedError("Invalid or expired reset token")
        user = await self.get_user(reset.user_id)
        user.password_hash = hash_password(new_password)
        reset.used_at = now
        await self.db.flush()
        return user
