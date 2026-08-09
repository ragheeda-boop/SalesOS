"""STORY-08-02: external_system_connections (OBJ-330) + tenant RLS.

Revision ID: e1a7b68c2d05
Revises: d0f6e89b1a37
Create Date: 2026-08-02

Tenant-scoped Integration Hub connections. Fernet credentials at app layer.
RLS FORCE via generate_policy_sql (app.tenant_id). Does NOT touch DEC-085
set_config / get_db(). No invented secrets.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "e1a7b68c2d05"
down_revision: str | None = "d0f6e89b1a37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "external_system_connections"


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("connector_key", sa.String(64), nullable=False),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("credential_ref", sa.String(512), nullable=False),
            sa.Column("credentials_encrypted", sa.Text(), nullable=True),
            sa.Column(
                "connection_config",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "cursor_state",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
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
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_external_system_connections_tenant_id",
            TABLE,
            ["tenant_id"],
        )
        op.create_index(
            "ix_external_system_connections_tenant_connector",
            TABLE,
            ["tenant_id", "connector_key"],
        )

    sql = generate_policy_sql(TABLE)
    for statement in sql.strip().split(";\n"):
        stmt = statement.strip()
        if stmt:
            op.execute(sa.text(stmt))


def downgrade() -> None:
    conn = op.get_bind()
    op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{TABLE}" ON "{TABLE}"'))
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" DISABLE ROW LEVEL SECURITY'))
    if _table_exists(conn, TABLE):
        op.drop_index("ix_external_system_connections_tenant_connector", table_name=TABLE)
        op.drop_index("ix_external_system_connections_tenant_id", table_name=TABLE)
        op.drop_table(TABLE)
