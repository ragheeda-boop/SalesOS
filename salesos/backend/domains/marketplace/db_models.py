"""SQLAlchemy ORM models for Marketplace domain."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base


class PluginModel(Base):
    __tablename__ = "marketplace_plugins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plugin_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(128), default="")
    license: Mapped[str] = mapped_column(String(32), default="MIT")
    icon: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    permissions: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    hooks: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    widgets: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    dependencies: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    config_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resource_limits: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    state: Mapped[str] = mapped_column(String(20), default="active", index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_marketplace_plugins_state", "state", "enabled"),
    )


class PluginLifecycleEventModel(Base):
    __tablename__ = "marketplace_lifecycle_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plugin_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    from_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_state: Mapped[str] = mapped_column(String(20), nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_marketplace_lifecycle_plugin_ts", "plugin_id", "timestamp"),
    )
