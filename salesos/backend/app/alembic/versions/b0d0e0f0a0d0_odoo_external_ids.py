"""Odoo Integration Foundation: external identity mapping table.

Revision ID: b0d0e0f0a0d0
Revises: ec0e98ec106b
Create Date: 2026-08-10

Maps Odoo record IDs to SalesOS canonical entities for idempotent sync.
Without this table, every Odoo sync would create duplicate records.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "b0d0e0f0a0d0"
down_revision: str | None = "ec0e98ec106b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "odoo_external_ids",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),

        sa.Column("odoo_model", sa.String(100), nullable=False),
        sa.Column("odoo_id", sa.Integer(), nullable=False),

        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),

        sa.Column("sync_status", sa.String(20), nullable=False, server_default="synced"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("odoo_write_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.execute(sa.text(
        "ALTER TABLE odoo_external_ids ADD CONSTRAINT uq_odoo_external "
        "UNIQUE (tenant_id, odoo_model, odoo_id)"
    ))

    op.create_index("idx_oex_tenant", "odoo_external_ids", ["tenant_id"])
    op.create_index("idx_oex_entity", "odoo_external_ids", ["entity_type", "entity_id"])
    op.create_index("idx_oex_odoo", "odoo_external_ids", ["odoo_model", "odoo_id"])
    op.create_index("idx_oex_tenant_status", "odoo_external_ids", ["tenant_id", "sync_status"])

    for stmt in generate_policy_sql("odoo_external_ids").strip().split(";\n"):
        if stmt.strip():
            op.execute(sa.text(stmt.strip()))


def downgrade() -> None:
    op.execute(sa.text('DROP POLICY IF EXISTS tenant_isolation_odoo_external_ids ON odoo_external_ids'))
    op.drop_table("odoo_external_ids")
