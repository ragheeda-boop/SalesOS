"""STORY-08-05: sync_runs (OBJ-332) + monthly partitions + tenant RLS.

Revision ID: c4d8e21a9f07
Revises: f2b8c79d3e06
Create Date: 2026-08-02

One row per scheduled sync execution. Monthly RANGE partitions on
started_at (SAAS §11.4). FORCE RLS via generate_policy_sql.
Does NOT touch DEC-085 set_config / get_db(). No invented secrets.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from scripts.generate_rls_policies import generate_policy_sql

revision: str = "c4d8e21a9f07"
down_revision: str | None = "f2b8c79d3e06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "sync_runs"


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def _month_bounds(year: int, month: int) -> tuple[str, str]:
    start = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month + 1, 1, tzinfo=UTC)
    return start.isoformat(), end.isoformat()


def _ensure_partitions() -> None:
    """Create monthly partitions for 2026-01 .. 2027-12 + DEFAULT overflow."""
    for year in (2026, 2027):
        for month in range(1, 13):
            name = f"sync_runs_{year}_{month:02d}"
            lo, hi = _month_bounds(year, month)
            op.execute(
                sa.text(
                    f'CREATE TABLE IF NOT EXISTS "{name}" '
                    f'PARTITION OF "{TABLE}" '
                    f"FOR VALUES FROM ('{lo}') TO ('{hi}')"
                )
            )
    op.execute(
        sa.text(
            f'CREATE TABLE IF NOT EXISTS "sync_runs_default" ' f'PARTITION OF "{TABLE}" DEFAULT'
        )
    )


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("scheduled_job_id", sa.String(64), nullable=True),
            sa.Column("model", sa.String(128), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("failure_class", sa.String(64), nullable=True),
            sa.Column(
                "cursor_before",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "cursor_after",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "records_pulled",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "records_written",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "records_failed",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "error_log",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.PrimaryKeyConstraint("id", "started_at"),
            postgresql_partition_by="RANGE (started_at)",
        )
        op.create_index(
            "ix_sync_runs_tenant_started",
            TABLE,
            ["tenant_id", "started_at"],
        )
        op.create_index(
            "ix_sync_runs_tenant_connection",
            TABLE,
            ["tenant_id", "connection_id"],
        )
        op.create_index(
            "ix_sync_runs_tenant_updated",
            TABLE,
            ["tenant_id", "updated_at"],
        )
        _ensure_partitions()

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
        # Dropping parent CASCADE drops monthly + default partitions.
        op.drop_index("ix_sync_runs_tenant_updated", table_name=TABLE)
        op.drop_index("ix_sync_runs_tenant_connection", table_name=TABLE)
        op.drop_index("ix_sync_runs_tenant_started", table_name=TABLE)
        op.drop_table(TABLE)
