import datetime
import uuid
from typing import Any

from sqlalchemy import Column, Index, Integer, String, DateTime, func, text
from sqlalchemy.dialects.postgresql import JSONB

from sdk.database import Base


class TimelineEventModel(Base):
    __tablename__ = "timeline_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(64), nullable=False)
    event_type = Column(String(100), nullable=False)
    data = Column(JSONB, nullable=True)
    actor = Column(String(255), nullable=True)
    tenant_id = Column(String(36), nullable=True)
    importance = Column(Integer, nullable=False, server_default="0")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        # Live expression indexes (0005/0027) — metadata register (DEC-130g)
        Index(
            "ix_timeline_entity",
            "entity_type",
            "entity_id",
            text("created_at DESC"),
        ),
        Index(
            "ix_timeline_tenant",
            "tenant_id",
            "entity_type",
            text("created_at DESC"),
        ),
        Index("ix_timeline_event_type", "entity_type", "entity_id", "event_type"),
        Index("ix_timeline_actor", "actor"),
        # ORM/5d additive name — keep if present in live DB
        Index("ix_timeline_tenant_created", "tenant_id", "created_at"),
    )
