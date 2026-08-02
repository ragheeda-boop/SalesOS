import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

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

from .models import (
    DeviceSession,
    PasswordResetToken,
    RefreshTokenFamily,
    Tenant,
    TokenBlacklist,
    User,
)
from .repositories import TenantRepository, UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return cast(bool, pwd_context.verify(plain_password, hashed_password))


def _hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def _generate_id() -> str:
    return secrets.token_urlsafe(16)


def _current_key_id() -> str:
    return "v2-rs256"


def create_access_token(user_id: str, tenant_id: str, jti: str | None = None) -> str:
    from app.modules.identity.jwks import create_rs256_token_payload

    expire = _now() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": jti or secrets.token_urlsafe(16),
        "exp": expire,
        "iat": _now(),
        "type": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "kid": _current_key_id(),
    }
    return create_rs256_token_payload(payload)


def create_refresh_token(user_id: str, tenant_id: str, jti: str | None = None) -> str:
    from app.modules.identity.jwks import create_rs256_token_payload

    expire = _now() + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": jti or secrets.token_urlsafe(16),
        "exp": expire,
        "iat": _now(),
        "type": "refresh",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "kid": _current_key_id(),
    }
    return create_rs256_token_payload(payload)


def decode_access_token(token: str) -> dict:
    from app.modules.identity.jwks import decode_token

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")
        return payload
    except ValueError:
        raise UnauthorizedError("Invalid or expired token") from None


def decode_refresh_token(token: str) -> dict:
    from app.modules.identity.jwks import decode_token

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        return payload
    except ValueError:
        raise UnauthorizedError("Invalid or expired refresh token") from None


def create_owner_access_token(user_id: str, jti: str | None = None) -> str:
    """Mint an Owner Platform access token (separate audience; not accepted by tenant API)."""
    from app.modules.identity.jwks import create_rs256_token_payload

    expire = _now() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "jti": jti or secrets.token_urlsafe(16),
        "exp": expire,
        "iat": _now(),
        "type": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_owner_audience,
        "kid": _current_key_id(),
    }
    return create_rs256_token_payload(payload)


def create_owner_refresh_token(user_id: str, jti: str | None = None) -> str:
    """Mint an Owner Platform refresh token (separate audience; not accepted by tenant API)."""
    from app.modules.identity.jwks import create_rs256_token_payload

    expire = _now() + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "jti": jti or secrets.token_urlsafe(16),
        "exp": expire,
        "iat": _now(),
        "type": "refresh",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_owner_audience,
        "kid": _current_key_id(),
    }
    return create_rs256_token_payload(payload)


def decode_owner_access_token(token: str) -> dict:
    """Verify an Owner Platform access token (owner audience only)."""
    from app.modules.identity.jwks import decode_token

    try:
        payload = decode_token(token, audience=settings.jwt_owner_audience)
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")
        return payload
    except ValueError:
        raise UnauthorizedError("Invalid or expired token") from None


def decode_owner_refresh_token(token: str) -> dict:
    """Verify an Owner Platform refresh token (owner audience only)."""
    from app.modules.identity.jwks import decode_token

    try:
        payload = decode_token(token, audience=settings.jwt_owner_audience)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        return payload
    except ValueError:
        raise UnauthorizedError("Invalid or expired refresh token") from None


class IdentityService:
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

    # ── Refresh Token Family Management ──────────────────────────────────

    async def create_token_family(
        self,
        user_id: str,
        tenant_id: str,
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
        self,
        refresh_token_jti: str,
        user_id: str,
        tenant_id: str,
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
            select(DeviceSession)
            .where(
                DeviceSession.user_id == user_id,
                DeviceSession.is_revoked.is_(False),
                DeviceSession.expires_at > _now(),
            )
            .order_by(DeviceSession.last_used_at.desc())
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
        if await self._tenant_repo.exists_by_slug(slug):
            raise DuplicateError("Tenant", "slug", slug)

        tenant = Tenant(name=name, slug=slug, domain=domain)
        await self._tenant_repo.save(tenant)

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
                    self.logger.warn(
                        "event.publish_failed", entity_type="tenant", aggregate_id=str(tenant.id)
                    )

        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant:
        try:
            return await self._tenant_repo.get(uuid.UUID(tenant_id))
        except Exception:
            raise NotFoundError("Tenant", tenant_id) from None

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        return await self._tenant_repo.get_by_slug(slug)

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        full_name_ar: str | None = None,
        tenant_id: str | None = None,
    ) -> User:
        if await self._user_repo.exists_by_email(email):
            raise DuplicateError("User", "email", email)

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            full_name_ar=full_name_ar,
            tenant_id=tenant_id,
        )
        await self._user_repo.save(user)

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
                    self.logger.warn(
                        "event.publish_failed", entity_type="user", aggregate_id=str(user.id)
                    )

        return user

    async def authenticate(self, email: str, password: str) -> User:
        # Email is globally unique, but FORCE RLS on users hides rows until
        # app.tenant_id is set. Probe via owner_engine (same split as init_db /
        # Alembic), then pin GUC on the request session before app-role reads.
        # Owner probe is best-effort: unit tests use a different asyncio loop /
        # SQLite session and must not crash on cross-loop asyncpg Futures.
        from sqlalchemy import text as sa_text
        from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

        from app.database import owner_engine, set_current_tenant_id

        tenant_id: str | None = None
        try:
            async with _AsyncSession(owner_engine, expire_on_commit=False) as owner_db:
                probe = await UserRepository(owner_db).get_by_email(email)
                tenant_id = str(probe.tenant_id) if probe and probe.tenant_id else None
        except Exception:
            tenant_id = None
        if tenant_id:
            set_current_tenant_id(tenant_id)
            await self.db.execute(
                sa_text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_id},
            )

        user = await self._user_repo.get_by_email(email)

        _MAX_FAILED_ATTEMPTS = 5
        _LOCK_DURATION_MINUTES = 15

        if user and user.is_locked:
            locked_until = user.locked_until
            if locked_until is None:
                raise UnauthorizedError("Account locked. | الحساب مقفل.")
            remaining = int((locked_until - _now()).total_seconds() / 60)
            audit = AuditTrail(self.db)
            await audit.record(
                tenant_id=str(user.tenant_id) if user.tenant_id else "",
                entity_type="user",
                entity_id=str(user.id),
                action="login_blocked_locked",
                metadata={"email": email, "locked_remaining_minutes": remaining},
            )
            if self.logger:
                self.logger.warn(
                    "auth.account_locked",
                    user_id=str(user.id),
                    email=email,
                    locked_until=str(user.locked_until),
                )
            raise UnauthorizedError(
                f"Account locked. Try again in {remaining} minutes. | "
                f"الحساب مقفل. حاول مرة أخرى بعد {remaining} دقيقة."
            )

        if not user or not verify_password(password, user.password_hash):
            if user:
                user.failed_attempts += 1
                if user.failed_attempts >= _MAX_FAILED_ATTEMPTS:
                    user.locked_until = _now() + timedelta(minutes=_LOCK_DURATION_MINUTES)
                    user.failed_attempts = 0
                    audit = AuditTrail(self.db)
                    await audit.record(
                        tenant_id=str(user.tenant_id) if user.tenant_id else "",
                        entity_type="user",
                        entity_id=str(user.id),
                        action="account_locked",
                        metadata={
                            "email": email,
                            "failed_attempts": _MAX_FAILED_ATTEMPTS,
                            "lock_duration_minutes": _LOCK_DURATION_MINUTES,
                        },
                    )
                    if self.logger:
                        self.logger.warn(
                            "auth.account_locked_after_failures",
                            user_id=str(user.id),
                            email=email,
                            failed_attempts=_MAX_FAILED_ATTEMPTS,
                        )
                    await self.db.flush()
                    raise UnauthorizedError(
                        "Account locked after 5 failed attempts. Try again in 15 minutes. | "
                        "تم قفل الحساب بعد 5 محاولات فاشلة. حاول مرة أخرى بعد 15 دقيقة."
                    )
                await self.db.flush()
            raise UnauthorizedError(
                "Invalid email or password | البريد الإلكتروني أو كلمة المرور غير صحيحة"
            )

        user.failed_attempts = 0
        user.locked_until = None
        user.last_login_at = _now()
        await self.db.flush()

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
                    self.logger.warn(
                        "event.publish_failed", entity_type="user", aggregate_id=str(user.id)
                    )

        return user

    async def get_user(self, user_id: str) -> User:
        try:
            return await self._user_repo.get(uuid.UUID(user_id))
        except Exception:
            raise NotFoundError("User", user_id) from None

    async def get_users_by_tenant(self, tenant_id: str) -> list[User]:
        users, _ = await self._user_repo.find_by_tenant(tenant_id, page=1, page_size=10000)
        return users

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
                    self.logger.warn(
                        "event.publish_failed", entity_type="user", aggregate_id=str(user.id)
                    )

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
                    self.logger.warn(
                        "event.publish_failed", entity_type="user", aggregate_id=str(user.id)
                    )

        return user

    async def forgot_password(self, email: str) -> str | None:
        """Generate a password reset token. Returns the raw token for delivery."""
        user = await self._user_repo.get_by_email(email)
        if not user:
            if self.logger:
                # Do not log the address or credential-adjacent wording (Semgrep logger-credential).
                self.logger.info("auth.reset_requested", outcome="unknown_identity")
            return None
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        now = datetime.now(UTC)
        reset = PasswordResetToken(
            id=secrets.token_urlsafe(16),
            user_id=str(user.id),
            token_hash=token_hash,
            expires_at=now + timedelta(hours=1),
        )
        self.db.add(reset)
        await self.db.flush()
        if self.logger:
            # Log opaque user id only — never the address or raw token.
            self.logger.info("auth.reset_token_created", user_id=str(user.id))
        return raw_token

    async def reset_password(self, token: str, new_password: str) -> User:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(UTC)
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
        user = await self.get_user(str(reset.user_id))
        user.password_hash = hash_password(new_password)
        reset.used_at = now
        await self.db.flush()
        return user

    async def delete_user(self, user_id: str, tenant_id: str) -> None:
        """PDPL/Right to Erasure — permanently delete user and anonymize personal data."""
        user = await self._user_repo.get(uuid.UUID(user_id))
        if not user:
            raise NotFoundError("User", user_id)

        # Revoke all sessions and tokens
        await self.revoke_all_user_sessions(user_id)

        # Anonymize personal data (PDPL Article 20: right to erasure)
        user.email = f"deleted-{user_id[:8]}@anonymized.salesos.io"
        user.full_name = "حذف المستخدم"
        user.full_name_ar = "حذف المستخدم"
        user.phone = None
        user.avatar_url = None
        user.preferences = {}
        user.is_active = False
        user.password_hash = hashlib.sha256(user_id.encode()).hexdigest()

        await self.db.flush()

        if self.event_bus:
            try:
                from sdk.events.domain_events import UserRegistered as UserDeleted

                await self.event_bus.publish(
                    UserDeleted(
                        tenant_id=tenant_id,
                        aggregate_id=user_id,
                        aggregate_type="user",
                    )
                )
            except Exception:
                if self.logger:
                    self.logger.warn(
                        "event.publish_failed", entity_type="user", aggregate_id=user_id
                    )

        if self.logger:
            self.logger.info(
                "User deleted (anonymized) per PDPL right to erasure: user_id=%s", user_id
            )
