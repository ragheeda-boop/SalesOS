"""STORY-08-02 — ExternalSystemConnection ORM (OBJ-330).

Tenant-scoped. Fernet credentials column + vault credential_ref.
RLS enabled in Alembic. Does NOT touch DEC-085 set_config helpers.
Not Production GO.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base


class ExternalSystemConnectionModel(Base):
    """OBJ-330 ExternalSystemConnection — tenant-owned connector binding."""

    __tablename__ = "external_system_connections"
    __table_args__ = (
        Index("ix_external_system_connections_tenant_id", "tenant_id"),
        Index(
            "ix_external_system_connections_tenant_connector",
            "tenant_id",
            "connector_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    connector_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Vault pointer only — never raw secrets.
    credential_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    # Optional Fernet envelope for secret material (GoogleAccount precedent).
    credentials_encrypted: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # Non-secret JSON only (validated in service).
    connection_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    # Per-model incremental watermarks (opaque strings).
    cursor_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
