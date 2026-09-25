from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "client_event_id",
            name="uq_telemetry_events_tenant_client_event_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    client_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    properties: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
