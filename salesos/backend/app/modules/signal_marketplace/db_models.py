"""SQLAlchemy tables for signal marketplace persistence (C.1)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base


class SignalCatalogModel(Base):
    __tablename__ = "signal_catalog"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ar_name: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    domain: Mapped[str] = mapped_column(String(64), nullable=False, server_default="", index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, server_default="")
    severity: Mapped[str] = mapped_column(String(20), nullable=False, server_default="info")
    source: Mapped[str] = mapped_column(String(128), nullable=False, server_default="")
    pack_id: Mapped[str] = mapped_column(String(64), nullable=False, server_default="", index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    weight: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.5")
    decay_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="90")
    triggers: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    relevance_sectors: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class SignalSubscriptionModel(Base):
    __tablename__ = "signal_subscriptions"
    __table_args__ = (
        Index("ix_signal_subs_tenant_signal", "tenant_id", "signal_id"),
        Index("ix_signal_subs_tenant_company", "tenant_id", "company_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    signal_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("signal_catalog.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, server_default="in-app")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class SignalEventModel(Base):
    __tablename__ = "signal_events"
    __table_args__ = (
        Index("ix_signal_events_tenant_detected", "tenant_id", "detected_at"),
        Index("ix_signal_events_tenant_company", "tenant_id", "company_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    signal_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("signal_catalog.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
