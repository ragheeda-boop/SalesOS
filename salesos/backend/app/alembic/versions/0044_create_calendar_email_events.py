"""Create employee_calendar_events and employee_email_events tables

Revision ID: 0044
Revises: 0043
Create Date: 2026-07-25

Foundation for Calendar Intelligence (Google/Microsoft) and Email Intelligence
(Gmail/Outlook) integrations. Tables store synced events per employee with full
metadata for KPI computation.
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0044"
down_revision: str | None = "0043"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def _index_exists(conn, table: str, index_name: str) -> bool:
    inspector = sa.inspect(conn)
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "employee_calendar_events"):
        op.create_table(
            "employee_calendar_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("provider", sa.String(20), nullable=False),
            sa.Column("provider_event_id", sa.String(255), nullable=False),
            sa.Column("title", sa.String(500), nullable=True),
            sa.Column("start_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("end_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("timezone_name", sa.String(50), nullable=True),
            sa.Column("duration_minutes", sa.Integer, server_default="0"),
            sa.Column("is_recurring", sa.Boolean, server_default="false"),
            sa.Column("recurrence_rule", sa.String(500), nullable=True),
            sa.Column("is_cancelled", sa.Boolean, server_default="false"),
            sa.Column("is_all_day", sa.Boolean, server_default="false"),
            sa.Column("attendees_count", sa.Integer, server_default="0"),
            sa.Column("is_internal", sa.Boolean, server_default="true"),
            sa.Column("conference_link", sa.String(1000), nullable=True),
            sa.Column("conference_provider", sa.String(50), nullable=True),
            sa.Column("organizer_email", sa.String(255), nullable=True),
            sa.Column("response_status", sa.String(20), server_default="accepted"),
            sa.Column("location", sa.String(1000), nullable=True),
            sa.Column("description_md", sa.Text, nullable=True),
            sa.Column("related_company_ids", JSONB, nullable=True, server_default="[]"),
            sa.Column("related_contact_ids", JSONB, nullable=True, server_default="[]"),
            sa.Column("related_opportunity_ids", JSONB, nullable=True, server_default="[]"),
            sa.Column("sync_token", sa.String(255), nullable=True),
            sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    for name, cols in (
        ("ix_cal_events_tenant_employee", ["tenant_id", "employee_id"]),
        ("ix_cal_events_tenant_employee_daterange", ["tenant_id", "employee_id", "start_utc", "end_utc"]),
        ("ix_cal_events_provider_event", ["provider", "provider_event_id"]),
        ("ix_cal_events_start_utc", ["start_utc"]),
    ):
        if _table_exists(conn, "employee_calendar_events") and not _index_exists(conn, "employee_calendar_events", name):
            op.create_index(name, "employee_calendar_events", cols)

    if not _table_exists(conn, "employee_email_events"):
        op.create_table(
            "employee_email_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("provider", sa.String(20), nullable=False),
            sa.Column("provider_message_id", sa.String(500), nullable=False),
            sa.Column("thread_id", sa.String(255), nullable=True),
            sa.Column("in_reply_to", sa.String(500), nullable=True),
            sa.Column("direction", sa.String(10), nullable=False),
            sa.Column("from_address", sa.String(500), nullable=True),
            sa.Column("to_addresses", JSONB, nullable=True, server_default="[]"),
            sa.Column("cc_addresses", JSONB, nullable=True, server_default="[]"),
            sa.Column("bcc_addresses", JSONB, nullable=True, server_default="[]"),
            sa.Column("subject", sa.String(1000), nullable=True),
            sa.Column("snippet", sa.Text, nullable=True),
            sa.Column("body_preview", sa.Text, nullable=True),
            sa.Column("has_attachments", sa.Boolean, server_default="false"),
            sa.Column("is_internal", sa.Boolean, server_default="true"),
            sa.Column("is_read", sa.Boolean, server_default="true"),
            sa.Column("labels", JSONB, nullable=True, server_default="[]"),
            sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("response_time_seconds", sa.Integer, nullable=True),
            sa.Column("related_company_ids", JSONB, nullable=True, server_default="[]"),
            sa.Column("related_contact_ids", JSONB, nullable=True, server_default="[]"),
            sa.Column("related_opportunity_ids", JSONB, nullable=True, server_default="[]"),
            sa.Column("ai_summary", sa.Text, nullable=True),
            sa.Column("ai_sentiment", sa.String(20), nullable=True),
            sa.Column("ai_action_items", JSONB, nullable=True, server_default="[]"),
            sa.Column("sync_history_id", sa.String(255), nullable=True),
            sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    for name, cols in (
        ("ix_email_events_tenant_employee", ["tenant_id", "employee_id"]),
        ("ix_email_events_tenant_employee_ts", ["tenant_id", "employee_id", "timestamp_utc"]),
        ("ix_email_events_provider_msg", ["provider", "provider_message_id"]),
        ("ix_email_events_thread", ["thread_id"]),
        ("ix_email_events_timestamp", ["timestamp_utc"]),
    ):
        if _table_exists(conn, "employee_email_events") and not _index_exists(conn, "employee_email_events", name):
            op.create_index(name, "employee_email_events", cols)


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "employee_email_events"):
        op.drop_table("employee_email_events")
    if _table_exists(conn, "employee_calendar_events"):
        op.drop_table("employee_calendar_events")
