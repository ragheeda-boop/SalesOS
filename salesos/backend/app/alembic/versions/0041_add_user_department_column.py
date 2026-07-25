"""Add department column to users table

Revision ID: 0041
Revises: 0040
Create Date: 2026-07-25

Idempotent: skips column if already exists.
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0041"
down_revision: str | None = "0040"
branch_labels: str | None = None
depends_on: str | None = None


def _col_exists(conn, table: str, column: str) -> bool:
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()

    if not _col_exists(conn, "users", "department"):
        op.add_column(
            "users",
            sa.Column("department", sa.String(100), nullable=True, server_default=None),
        )
    if not _col_exists(conn, "users", "department"):
        pass


def downgrade() -> None:
    conn = op.get_bind()
    if _col_exists(conn, "users", "department"):
        op.drop_column("users", "department")
