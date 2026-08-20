"""Phase 1 Product Core — Reviews domain table.

Creates:
  - commercial_reviews: review workflows for deals, quotes, proposals

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commercial_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("review_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("assigned_to", sa.String(36), nullable=True),
        sa.Column("requested_by", sa.String(36), nullable=True),
        sa.Column("decisions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    op.create_index("ix_commercial_reviews_tenant_status", "commercial_reviews",
                    ["tenant_id", "status"])
    op.create_index("ix_commercial_reviews_target", "commercial_reviews",
                    ["target_type", "target_id"])
    op.create_index("ix_commercial_reviews_assigned", "commercial_reviews",
                    ["assigned_to"])


def downgrade() -> None:
    op.drop_index("ix_commercial_reviews_assigned", table_name="commercial_reviews")
    op.drop_index("ix_commercial_reviews_target", table_name="commercial_reviews")
    op.drop_index("ix_commercial_reviews_tenant_status", table_name="commercial_reviews")
    op.drop_table("commercial_reviews")
