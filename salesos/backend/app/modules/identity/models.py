import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdk.database import Base, BaseModel


class Tenant(BaseModel):
    __tablename__ = "tenants"
    # Live DB (0001): UniqueConstraint tenants_slug_key + non-unique ix_tenants_slug
    # (DEC-130g — avoid unique=True+index=True which invents unique ix_tenants_slug)
    __table_args__ = (
        UniqueConstraint("slug", name="tenants_slug_key"),
        Index("ix_tenants_slug", "slug"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    # STORY-04-01 Owner Platform extension (opaque catalog id; keep plan label)
    plan_id: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    data_residency: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    provisioning_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # STORY-04-04: soft-delete retention clock (column; settings key kept as dual-write)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict | None] = mapped_column(type_=JSONB, default=dict)
    features: Mapped[dict | None] = mapped_column(type_=JSONB, default=dict)
    subscription_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        # noload: selectin after Tenant flush hung Railway register (~60s).
        # Do not reintroduce selectin without an explicit load strategy at call site.
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"


class User(BaseModel):
    __tablename__ = "users"
    # Live DB (0001): UniqueConstraint users_email_key + non-unique ix_users_email (DEC-130g)
    __table_args__ = (
        UniqueConstraint("email", name="users_email_key"),
        Index("ix_users_email", "email"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name_ar: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")
    department: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(30))
    preferences: Mapped[dict | None] = mapped_column(type_=JSONB, default=dict)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="users")

    @property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return bool(self.locked_until > datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RefreshTokenFamily(Base):
    __tablename__ = "refresh_token_families"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    family_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_compromised: Mapped[bool] = mapped_column(Boolean, default=False)


class DeviceSession(Base):
    __tablename__ = "device_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    refresh_family_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("refresh_token_families.id"), nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(512), default="")
    device_type: Mapped[str] = mapped_column(String(50), default="unknown")
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("ix_device_sessions_tenant", "tenant_id"),
        Index("ix_device_sessions_expires", "expires_at"),
    )


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_type: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_token_blacklist_expires", "expires_at"),)
