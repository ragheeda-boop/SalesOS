"""STORY-04-04: tenants.deleted_at retention column + settings backfill.

Revision ID: d4b0e23f5a91
Revises: c3a9f12d4e80
Create Date: 2026-08-02

Additive column only. Does NOT touch DEC-085 / RLS policies.
Backfill from settings->>'deletion_requested_at' when parseable.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4b0e23f5a91"
down_revision: Union[str, None] = "c3a9f12d4e80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    return row is not None


def _index_exists(conn, name: str) -> bool:
    row = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"),
        {"n": name},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _column_exists(conn, "tenants", "deleted_at"):
        op.add_column(
            "tenants",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _index_exists(conn, "ix_tenants_deleted_at"):
        op.create_index("ix_tenants_deleted_at", "tenants", ["deleted_at"])
    # Backfill from interim settings stamp (STORY-04-04 fd5af4d).
    op.execute(
        sa.text(
            """
            UPDATE tenants
            SET deleted_at = (settings->>'deletion_requested_at')::timestamptz
            WHERE deleted_at IS NULL
              AND settings ? 'deletion_requested_at'
              AND NULLIF(settings->>'deletion_requested_at', '') IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    if _index_exists(conn, "ix_tenants_deleted_at"):
        op.drop_index("ix_tenants_deleted_at", table_name="tenants")
    if _column_exists(conn, "tenants", "deleted_at"):
        op.drop_column("tenants", "deleted_at")
