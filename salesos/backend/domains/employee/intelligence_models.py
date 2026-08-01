"""Employee calendar events and email events database models.

These tables store synced calendar events and email interactions per employee,
ready for Google Workspace / Microsoft 365 OAuth integration.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean, Text, func, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.common.models import Base


class EmployeeCalendarEventModel(Base):
    """Per-employee calendar events synced from Google/Microsoft."""

    __tablename__ = "employee_calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(20), nullable=False)  # google, microsoft, caldav
    provider_event_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=True)
    start_utc = Column(DateTime(timezone=True), nullable=False)
    end_utc = Column(DateTime(timezone=True), nullable=False)
    timezone_name = Column(String(50), nullable=True)
    duration_minutes = Column(Integer, default=0)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(500), nullable=True)
    is_cancelled = Column(Boolean, default=False)
    is_all_day = Column(Boolean, default=False)
    attendees_count = Column(Integer, default=0)
    is_internal = Column(Boolean, default=True)  # all attendees same tenant?
    conference_link = Column(String(1000), nullable=True)
    conference_provider = Column(String(50), nullable=True)  # zoom, meet, teams
    organizer_email = Column(String(255), nullable=True)
    response_status = Column(String(20), default="accepted")  # accepted, declined, tentative
    location = Column(String(1000), nullable=True)
    description_md = Column(Text, nullable=True)
    related_company_ids = Column(JSONB, nullable=True, default=list)
    related_contact_ids = Column(JSONB, nullable=True, default=list)
    related_opportunity_ids = Column(JSONB, nullable=True, default=list)
    sync_token = Column(String(255), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_cal_events_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_cal_events_tenant_employee_daterange", "tenant_id", "employee_id", "start_utc", "end_utc"),
        Index("ix_cal_events_provider_event", "provider", "provider_event_id"),
        Index("ix_cal_events_start_utc", "start_utc"),
        # Live unique (0049) — register to silence remove_index (DEC-130g)
        Index(
            "uq_cal_events_tenant_provider_event",
            "tenant_id",
            "provider",
            "provider_event_id",
            unique=True,
        ),
    )


class EmployeeEmailEventModel(Base):
    """Per-employee email events synced from Gmail/Outlook."""

    __tablename__ = "employee_email_events"

    id = Column(UUID(as_uuid=True), primary_key=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(20), nullable=False)  # google, microsoft, imap
    provider_message_id = Column(String(500), nullable=False)
    thread_id = Column(String(255), nullable=True)
    in_reply_to = Column(String(500), nullable=True)
    direction = Column(String(10), nullable=False)  # sent, received
    from_address = Column(String(500), nullable=True)
    to_addresses = Column(JSONB, nullable=True, default=list)
    cc_addresses = Column(JSONB, nullable=True, default=list)
    bcc_addresses = Column(JSONB, nullable=True, default=list)
    subject = Column(String(1000), nullable=True)
    snippet = Column(Text, nullable=True)
    body_preview = Column(Text, nullable=True)
    has_attachments = Column(Boolean, default=False)
    is_internal = Column(Boolean, default=True)
    is_read = Column(Boolean, default=True)
    labels = Column(JSONB, nullable=True, default=list)  # gmail labels / outlook categories
    timestamp_utc = Column(DateTime(timezone=True), nullable=False)
    response_time_seconds = Column(Integer, nullable=True)  # time from received to response
    related_company_ids = Column(JSONB, nullable=True, default=list)
    related_contact_ids = Column(JSONB, nullable=True, default=list)
    related_opportunity_ids = Column(JSONB, nullable=True, default=list)
    ai_summary = Column(Text, nullable=True)
    ai_sentiment = Column(String(20), nullable=True)  # positive, neutral, negative
    ai_action_items = Column(JSONB, nullable=True, default=list)
    sync_history_id = Column(String(255), nullable=True)  # gmail historyId for incremental sync
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_email_events_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_email_events_tenant_employee_ts", "tenant_id", "employee_id", "timestamp_utc"),
        Index("ix_email_events_provider_msg", "provider", "provider_message_id"),
        Index("ix_email_events_thread", "thread_id"),
        Index("ix_email_events_timestamp", "timestamp_utc"),
        # Live unique (0049) — register to silence remove_index (DEC-130g)
        Index(
            "uq_email_events_tenant_provider_msg",
            "tenant_id",
            "provider",
            "provider_message_id",
            unique=True,
        ),
    )
