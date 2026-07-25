"""Add deleted_at column to users table for GDPR-compliant soft delete

Revision ID: 0043
Revises: 0042
Create Date: 2026-07-25

Supports GDPR right-to-erasure: marks records as deleted without
destroying audit history. Retention policy can purge records where
deleted_at > retention_period (e.g., 90 days).
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: str | None = None
depends_on: str | None = None


def _col_exists(conn, table: str, column: str) -> bool:
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()
    if not _col_exists(conn, "users", "deleted_at"):
        op.add_column(
            "users",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, server_default=None),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _col_exists(conn, "users", "deleted_at"):
        op.drop_column("users", "deleted_at")
