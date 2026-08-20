"""Phase 2 Intelligence — Evidence chain tables.

Creates:
  - commercial_insights: insights backed by evidence chain
  - commercial_evidence_items: individual evidence items linked to insights

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-19
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── commercial_insights ──
    op.create_table(
        "commercial_insights",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("target_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=False, index=True),
        sa.Column("overall_confidence", sa.Float(), server_default="0.0"),
        sa.Column("confidence_level", sa.String(20), server_default="unknown"),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_commercial_insights_tenant_category", "commercial_insights", ["tenant_id", "category"])
    op.create_index("ix_commercial_insights_tenant_confidence", "commercial_insights", ["tenant_id", "confidence_level"])

    # ── commercial_evidence_items ──
    op.create_table(
        "commercial_evidence_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("insight_id", sa.String(36), nullable=False, index=True),
        sa.Column("evidence_type", sa.String(50), nullable=False, index=True),
        sa.Column("source_domain", sa.String(50), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(36), server_default=""),
        sa.Column("source_name", sa.String(200), server_default=""),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.0"),
        sa.Column("confidence_level", sa.String(20), server_default="unknown"),
        sa.Column("data", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_commercial_evidence_insight", "commercial_evidence_items", ["insight_id"])
    op.create_index("ix_commercial_evidence_type", "commercial_evidence_items", ["evidence_type"])


def downgrade() -> None:
    op.drop_table("commercial_evidence_items")
    op.drop_table("commercial_insights")
