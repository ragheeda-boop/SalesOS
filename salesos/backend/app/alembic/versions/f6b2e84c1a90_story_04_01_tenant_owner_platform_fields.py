"""STORY-04-01: Tenant Owner Platform extension fields.

Revision ID: f6b2e84c1a90
Revises: a4f7c29e1b80
Create Date: 2026-08-02

Phase 1 Stream A — additive columns on ``tenants``:
  plan_id, region, data_residency, provisioning_status, trial_ends_at

Backfill: existing rows → provisioning_status='active'.
Does NOT touch DEC-085 set_config / RLS policy definitions.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6b2e84c1a90"
down_revision: Union[str, None] = "a4f7c29e1b80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLS: list[tuple[str, sa.types.TypeEngine, dict]] = [
    ("plan_id", sa.String(64), {"nullable": True}),
    ("region", sa.String(32), {"nullable": True}),
    ("data_residency", sa.String(32), {"nullable": True}),
    (
        "provisioning_status",
        sa.String(32),
        {"nullable": False, "server_default": "pending"},
    ),
    ("trial_ends_at", sa.DateTime(timezone=True), {"nullable": True}),
]


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()
    for name, col_type, kwargs in _COLS:
        if not _column_exists(conn, "tenants", name):
            op.add_column("tenants", sa.Column(name, col_type, **kwargs))

    # Existing tenants are already live — mark active (Sprint-04 backfill default).
    op.execute(
        sa.text(
            "UPDATE tenants SET provisioning_status = 'active' "
            "WHERE provisioning_status = 'pending' OR provisioning_status IS NULL"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    for name, _col_type, _kwargs in reversed(_COLS):
        if _column_exists(conn, "tenants", name):
            op.drop_column("tenants", name)
