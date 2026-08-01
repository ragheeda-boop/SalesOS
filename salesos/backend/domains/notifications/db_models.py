"""SQLAlchemy ORM models for Notifications domain."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # DB nullable with defaults (DEC-130d — ORM align; no SET NOT NULL)
    body: Mapped[str | None] = mapped_column(Text, nullable=True, default="")
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    read: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read", "created_at"),
        Index("ix_notifications_tenant_type", "tenant_id", "type"),
    )
