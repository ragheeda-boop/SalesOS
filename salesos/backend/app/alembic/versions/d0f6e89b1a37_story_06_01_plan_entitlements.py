"""STORY-06-01: admin_plans.entitlements JSONB + tier backfill.

Revision ID: d0f6e89b1a37
Revises: c9e5d78a0f26
Create Date: 2026-08-02

Additive. No RLS. No DEC-085. No secrets.
"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d0f6e89b1a37"
down_revision: Union[str, None] = "c9e5d78a0f26"
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
    if not _table_exists(conn, "admin_plans"):
        return
    if not _column_exists(conn, "admin_plans", "entitlements"):
        op.add_column(
            "admin_plans",
            sa.Column(
                "entitlements",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        )

    # Backfill empty docs from commercial defaults (import pure module).
    from app.modules.admin.entitlements import (
        default_entitlements_for_tier,
        entitlements_to_dict,
    )

    rows = conn.execute(sa.text("SELECT id, tier, entitlements FROM admin_plans")).fetchall()
    for row in rows:
        plan_id, tier, ents = row[0], row[1], row[2]
        if isinstance(ents, dict) and ents.get("version") == 1 and ents.get("domains"):
            continue
        doc = entitlements_to_dict(default_entitlements_for_tier(str(tier or "free")))
        conn.execute(
            sa.text("UPDATE admin_plans SET entitlements = CAST(:e AS jsonb) WHERE id = :id"),
            {"e": json.dumps(doc), "id": str(plan_id)},
        )


def downgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "admin_plans"):
        return
    if _column_exists(conn, "admin_plans", "entitlements"):
        op.drop_column("admin_plans", "entitlements")
