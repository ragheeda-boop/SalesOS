"""Phase 3 HITL — Approval request tables.

Creates:
  - approval_requests: human-in-the-loop approval workflow for AI recommendations

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-19
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=False, index=True),
        sa.Column("target_id", sa.String(36), nullable=False, index=True),
        sa.Column("requested_by", sa.String(36), server_default="system"),
        sa.Column("action_summary", sa.Text(), server_default=""),
        sa.Column("action_evidence", sa.JSON(), server_default="[]"),
        sa.Column("required_level", sa.String(20), server_default="manager"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("assigned_to", sa.String(36), server_default=""),
        sa.Column("decisions", sa.JSON(), server_default="[]"),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("priority", sa.Float(), server_default="5.0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_approval_requests_tenant_status", "approval_requests", ["tenant_id", "status"])
    op.create_index("ix_approval_requests_tenant_target", "approval_requests", ["tenant_id", "target_type", "target_id"])
    op.create_index("ix_approval_requests_assigned", "approval_requests", ["tenant_id", "assigned_to", "status"])


def downgrade() -> None:
    op.drop_table("approval_requests")
