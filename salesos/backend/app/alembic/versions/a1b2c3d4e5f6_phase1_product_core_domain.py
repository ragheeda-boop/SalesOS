"""Phase 1 Product Core — Domain Model unification.

Adds:
  - companies.owner_id: account ownership (UUID FK → users.id, nullable)
  - companies.segment: account segmentation (String, nullable)
  - Deprecates UBOM DealObject (dead code, table never created)
  - Deprecates revenue_execution.opportunities (dual-table residual)

Revision ID: a1b2c3d4e5f6
Revises: f8b3d4e5f6a7
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f8b3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── P1-1: Add owner_id to companies ──
    op.add_column(
        "companies",
        sa.Column("owner_id", sa.UUID(), nullable=True),
    )
    op.create_index("ix_companies_owner", "companies", ["owner_id"])

    # ── P1-2: Add segment to companies ──
    op.add_column(
        "companies",
        sa.Column("segment", sa.String(50), nullable=True),
    )
    op.create_index("ix_companies_segment", "companies", ["segment"])
    op.create_index(
        "ix_companies_tenant_segment", "companies", ["tenant_id", "segment"]
    )

    # ── P1-3: Deprecate revenue_execution opportunities table ──
    # Add deprecation marker column (soft deprecation, no data loss)
    op.add_column(
        "opportunities",
        sa.Column(
            "_deprecated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="DEPRECATED: Use commercial_opportunities. This table is保留 for migration only.",
        ),
    )


def downgrade() -> None:
    op.drop_column("opportunities", "_deprecated")
    op.drop_index("ix_companies_tenant_segment", table_name="companies")
    op.drop_index("ix_companies_segment", table_name="companies")
    op.drop_column("companies", "segment")
    op.drop_index("ix_companies_owner", table_name="companies")
    op.drop_column("companies", "owner_id")
