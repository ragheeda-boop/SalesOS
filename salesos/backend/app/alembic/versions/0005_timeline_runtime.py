"""universal timeline: add timeline_entries table

Creates:
  - public.timeline_entries (universal timeline for all entity types)

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "timeline_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("data", postgresql.JSONB, nullable=True),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("tenant_id", sa.String(36), nullable=True),
        sa.Column("importance", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_timeline_entity", "timeline_entries",
                    ["entity_type", "entity_id", sa.text("created_at DESC")])
    op.create_index("ix_timeline_tenant", "timeline_entries",
                    ["tenant_id", "entity_type", sa.text("created_at DESC")])
    op.create_index("ix_timeline_event_type", "timeline_entries",
                    ["entity_type", "entity_id", "event_type"])


def downgrade() -> None:
    op.drop_table("timeline_entries")
