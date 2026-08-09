"""ADR-030: opportunity_contacts junction table — Canonical Opportunity <-> Contact relationship.

Revision ID: a1b9c8d7e6f5
Revises: f7a1b82c3d09
Create Date: 2026-08-09

RLS applied inline (Path B) following f7a1b82c3d09 pattern.
opportunity_id FK deferred — String(36) vs UUID type mismatch per ADR-030 readiness check.
contact_id CASCADE — junction rows without parent contact are meaningless.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "a1b9c8d7e6f5"
down_revision: str | None = "f7a1b82c3d09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def _index_exists(conn, table: str, index_name: str) -> bool:
    if not _table_exists(conn, table):
        return False
    return any(idx["name"] == index_name for idx in sa.inspect(conn).get_indexes(table))


def _apply_rls(table: str) -> None:
    sql = generate_policy_sql(table)
    for statement in sql.strip().split(";\n"):
        stmt = statement.strip()
        if stmt:
            op.execute(sa.text(stmt))


def _drop_rls_policy(table: str) -> None:
    policy_name = f"tenant_isolation_{table}"
    op.execute(sa.text(f'DROP POLICY IF EXISTS "{policy_name}" ON "{table}";'))


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "opportunity_contacts"):
        op.create_table(
            "opportunity_contacts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "tenant_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("opportunity_id", sa.String(36), nullable=False),
            sa.Column(
                "contact_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("contacts.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role", sa.String(50), nullable=True),
            sa.Column("is_primary", sa.Boolean, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not _index_exists(conn, "opportunity_contacts", "ix_opportunity_contacts_lookup"):
        op.create_index(
            "ix_opportunity_contacts_lookup",
            "opportunity_contacts",
            ["tenant_id", "opportunity_id", "contact_id"],
            unique=True,
        )
    if not _index_exists(conn, "opportunity_contacts", "ix_oc_tenant"):
        op.create_index("ix_oc_tenant", "opportunity_contacts", ["tenant_id"])
    if not _index_exists(conn, "opportunity_contacts", "ix_oc_tenant_opp"):
        op.create_index("ix_oc_tenant_opp", "opportunity_contacts", ["tenant_id", "opportunity_id"])
    if not _index_exists(conn, "opportunity_contacts", "ix_oc_contact"):
        op.create_index("ix_oc_contact", "opportunity_contacts", ["contact_id"])

    _apply_rls("opportunity_contacts")


def downgrade() -> None:
    conn = op.get_bind()
    _drop_rls_policy("opportunity_contacts")
    if _table_exists(conn, "opportunity_contacts"):
        op.drop_table("opportunity_contacts")
