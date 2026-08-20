"""Phase 1 Product Core — Quota + Territory Postgres tables.

Creates:
  - commercial_quotas: revenue targets per rep per period
  - commercial_territories: sales territories with assigned accounts

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── commercial_quotas ──
    op.create_table(
        "commercial_quotas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("rep_id", sa.String(36), nullable=False, index=True),
        sa.Column("rep_name", sa.String(200), nullable=True),
        sa.Column("period", sa.String(20), nullable=False, server_default="quarterly"),
        sa.Column("target_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("attained_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    op.create_index("ix_commercial_quotas_tenant_status", "commercial_quotas",
                    ["tenant_id", "status"])
    op.create_index("ix_commercial_quotas_tenant_rep", "commercial_quotas",
                    ["tenant_id", "rep_id"])

    # ── commercial_territories ──
    op.create_table(
        "commercial_territories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("region", sa.String(200), nullable=True),
        sa.Column("rep_id", sa.String(36), nullable=True, index=True),
        sa.Column("rep_name", sa.String(200), nullable=True),
        sa.Column("account_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    op.create_index("ix_commercial_territories_tenant_rep", "commercial_territories",
                    ["tenant_id", "rep_id"])
    op.create_index("ix_commercial_territories_tenant_region", "commercial_territories",
                    ["tenant_id", "region"])


def downgrade() -> None:
    op.drop_index("ix_commercial_territories_tenant_region", table_name="commercial_territories")
    op.drop_index("ix_commercial_territories_tenant_rep", table_name="commercial_territories")
    op.drop_table("commercial_territories")
    op.drop_index("ix_commercial_quotas_tenant_rep", table_name="commercial_quotas")
    op.drop_index("ix_commercial_quotas_tenant_status", table_name="commercial_quotas")
    op.drop_table("commercial_quotas")
