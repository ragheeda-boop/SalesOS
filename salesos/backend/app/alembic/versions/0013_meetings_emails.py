"""meetings and emails tables for Meeting Intelligence and Email domains

Creates:
  - meetings — meeting records linked to opportunities
  - emails — email records linked to opportunities

Revision ID: 0013
Revises: 020cfcbab7b4
Create Date: 2026-07-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: Union[str, None] = "020cfcbab7b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("meeting_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "emails",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False, index=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("from_address", sa.String(254), nullable=False),
        sa.Column("to_addresses", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("direction", sa.String(10), nullable=False, server_default="outbound"),
        sa.Column("email_type", sa.String(50), nullable=False, server_default="general"),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_meetings_opportunity", "meetings", ["opportunity_id", "tenant_id"])
    op.create_index("ix_emails_opportunity", "emails", ["opportunity_id", "tenant_id"])


def downgrade() -> None:
    op.drop_table("emails")
    op.drop_table("meetings")
