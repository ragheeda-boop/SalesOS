import datetime
import uuid
from typing import Any

from sqlalchemy import Column, Integer, String, DateTime, func
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
