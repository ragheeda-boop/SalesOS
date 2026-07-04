"""activity runtime: create activity_records table

Creates:
  - activity_records — unified activity spine for all business actions

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activity_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("actor", sa.String(255), nullable=False, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.String(64), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False, index=True),
    )
    op.create_index("ix_activity_entity", "activity_records",
                    ["entity_type", "entity_id", sa.text("timestamp DESC")])
    op.create_index("ix_activity_tenant_action", "activity_records",
                    ["tenant_id", "action", sa.text("timestamp DESC")])
    op.create_index("ix_activity_actor", "activity_records",
                    ["actor", sa.text("timestamp DESC")])
    op.create_index("ix_activity_action", "activity_records",
                    ["action", sa.text("timestamp DESC")])


def downgrade() -> None:
    op.drop_table("activity_records")
