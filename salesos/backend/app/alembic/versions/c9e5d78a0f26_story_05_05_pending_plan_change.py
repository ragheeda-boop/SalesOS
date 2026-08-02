"""STORY-05-05: subscriptions pending plan change columns.

Revision ID: c9e5d78a0f26
Revises: b8f4c67d9e15
Create Date: 2026-08-02

Additive. No RLS. No DEC-085. No secrets.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9e5d78a0f26"
down_revision: Union[str, None] = "b8f4c67d9e15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def _column_exists(conn, table: str, column: str) -> bool:
    if not _table_exists(conn, table):
        return False
    return column in {c["name"] for c in sa.inspect(conn).get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "subscriptions"):
        return
    if not _column_exists(conn, "subscriptions", "pending_plan_id"):
        op.add_column(
            "subscriptions",
            sa.Column("pending_plan_id", sa.String(64), nullable=True),
        )
    if not _column_exists(conn, "subscriptions", "pending_effective_at"):
        op.add_column(
            "subscriptions",
            sa.Column("pending_effective_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "subscriptions"):
        return
    if _column_exists(conn, "subscriptions", "pending_effective_at"):
        op.drop_column("subscriptions", "pending_effective_at")
    if _column_exists(conn, "subscriptions", "pending_plan_id"):
        op.drop_column("subscriptions", "pending_plan_id")
