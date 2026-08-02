"""STORY-05-04: dunning_cases table (grace → auto-suspend).

Revision ID: b8f4c67d9e15
Revises: a7e3b56c8d04
Create Date: 2026-08-02

Additive Owner-plane only. No RLS. No DEC-085. No secrets.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8f4c67d9e15"
down_revision: Union[str, None] = "a7e3b56c8d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def upgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "dunning_cases"):
        return
    op.create_table(
        "dunning_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grace_ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_stripe_invoice_id", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_dunning_cases_tenant_id", "dunning_cases", ["tenant_id"])
    op.create_index(
        "ix_dunning_cases_status_grace",
        "dunning_cases",
        ["status", "grace_ends_at"],
    )


def downgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "dunning_cases"):
        return
    op.drop_index("ix_dunning_cases_status_grace", table_name="dunning_cases")
    op.drop_index("ix_dunning_cases_tenant_id", table_name="dunning_cases")
    op.drop_table("dunning_cases")
