"""STORY-08-03: field_mapping_configs (OBJ-331) + tenant RLS.

Revision ID: f2b8c79d3e06
Revises: e1a7b68c2d05
Create Date: 2026-08-02

Versioned FieldMappingConfig per connection/model. FORCE RLS via
generate_policy_sql. Does NOT touch DEC-085 set_config / get_db().
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "f2b8c79d3e06"
down_revision: str | None = "e1a7b68c2d05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "field_mapping_configs"


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("model", sa.String(128), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column(
                "mappings",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "baseline_fields",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
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
            sa.ForeignKeyConstraint(
                ["connection_id"],
                ["external_system_connections.id"],
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "connection_id",
                "model",
                "version",
                name="uq_field_mapping_configs_conn_model_version",
            ),
        )
        op.create_index("ix_field_mapping_configs_tenant_id", TABLE, ["tenant_id"])
        op.create_index(
            "ix_field_mapping_configs_tenant_connection",
            TABLE,
            ["tenant_id", "connection_id"],
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
        op.drop_index("ix_field_mapping_configs_tenant_connection", table_name=TABLE)
        op.drop_index("ix_field_mapping_configs_tenant_id", table_name=TABLE)
        op.drop_table(TABLE)
