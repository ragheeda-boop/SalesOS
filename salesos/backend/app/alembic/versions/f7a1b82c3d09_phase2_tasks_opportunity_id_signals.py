"""Phase-2 C.4 task.opportunity_id + C.1 signal marketplace tables.

Revision ID: f7a1b82c3d09
Revises: e5f9a32b0c08
Create Date: 2026-08-08

Does NOT alter DEC-044 ALL_TENANT_TABLES (47). RLS for tenant-scoped signal
tables is applied in this migration via generate_policy_sql (same pattern as
e5f9 conflict_resolution_policies). Production upgrade not run from this file.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from scripts.generate_rls_policies import generate_policy_sql

revision: str = "f7a1b82c3d09"
down_revision: str | None = "e5f9a32b0c08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def _column_exists(conn, table: str, column: str) -> bool:
    if not _table_exists(conn, table):
        return False
    return any(c["name"] == column for c in sa.inspect(conn).get_columns(table))


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


def upgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "tasks") and not _column_exists(conn, "tasks", "opportunity_id"):
        op.add_column("tasks", sa.Column("opportunity_id", sa.String(36), nullable=True))
    if _table_exists(conn, "tasks") and not _index_exists(
        conn, "tasks", "ix_tasks_tenant_opportunity"
    ):
        op.create_index("ix_tasks_tenant_opportunity", "tasks", ["tenant_id", "opportunity_id"])

    if not _table_exists(conn, "signal_catalog"):
        op.create_table(
            "signal_catalog",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("ar_name", sa.String(255), nullable=False, server_default=""),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("domain", sa.String(64), nullable=False, server_default=""),
            sa.Column("category", sa.String(64), nullable=False, server_default=""),
            sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
            sa.Column("source", sa.String(128), nullable=False, server_default=""),
            sa.Column("pack_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
            sa.Column("weight", sa.Float(), nullable=False, server_default="0.5"),
            sa.Column("decay_days", sa.Integer(), nullable=False, server_default="90"),
            sa.Column(
                "triggers",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "relevance_sectors",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_signal_catalog_domain", "signal_catalog", ["domain"])
        op.create_index("ix_signal_catalog_pack_id", "signal_catalog", ["pack_id"])

    if not _table_exists(conn, "signal_subscriptions"):
        op.create_table(
            "signal_subscriptions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "signal_id",
                sa.String(64),
                sa.ForeignKey("signal_catalog.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("company_id", sa.String(36), nullable=False),
            sa.Column("tenant_id", sa.String(36), nullable=False),
            sa.Column("channel", sa.String(32), nullable=False, server_default="in-app"),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        )
        op.create_index("ix_signal_subscriptions_tenant_id", "signal_subscriptions", ["tenant_id"])
        op.create_index(
            "ix_signal_subs_tenant_signal",
            "signal_subscriptions",
            ["tenant_id", "signal_id"],
        )
        op.create_index(
            "ix_signal_subs_tenant_company",
            "signal_subscriptions",
            ["tenant_id", "company_id"],
        )
        _apply_rls("signal_subscriptions")

    if not _table_exists(conn, "signal_events"):
        op.create_table(
            "signal_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "signal_id",
                sa.String(64),
                sa.ForeignKey("signal_catalog.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("company_id", sa.String(36), nullable=False),
            sa.Column("tenant_id", sa.String(36), nullable=False),
            sa.Column(
                "data",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "detected_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_signal_events_tenant_id", "signal_events", ["tenant_id"])
        op.create_index(
            "ix_signal_events_tenant_detected",
            "signal_events",
            ["tenant_id", "detected_at"],
        )
        op.create_index(
            "ix_signal_events_tenant_company",
            "signal_events",
            ["tenant_id", "company_id"],
        )
        _apply_rls("signal_events")


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "signal_events"):
        op.execute(sa.text('DROP POLICY IF EXISTS "tenant_isolation_signal_events" ON "signal_events"'))
        op.execute(sa.text('ALTER TABLE "signal_events" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text('ALTER TABLE "signal_events" DISABLE ROW LEVEL SECURITY'))
        op.drop_index("ix_signal_events_tenant_company", table_name="signal_events")
        op.drop_index("ix_signal_events_tenant_detected", table_name="signal_events")
        op.drop_index("ix_signal_events_tenant_id", table_name="signal_events")
        op.drop_table("signal_events")
    if _table_exists(conn, "signal_subscriptions"):
        op.execute(
            sa.text(
                'DROP POLICY IF EXISTS "tenant_isolation_signal_subscriptions" '
                'ON "signal_subscriptions"'
            )
        )
        op.execute(sa.text('ALTER TABLE "signal_subscriptions" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text('ALTER TABLE "signal_subscriptions" DISABLE ROW LEVEL SECURITY'))
        op.drop_index("ix_signal_subs_tenant_company", table_name="signal_subscriptions")
        op.drop_index("ix_signal_subs_tenant_signal", table_name="signal_subscriptions")
        op.drop_index("ix_signal_subscriptions_tenant_id", table_name="signal_subscriptions")
        op.drop_table("signal_subscriptions")
    if _table_exists(conn, "signal_catalog"):
        op.drop_index("ix_signal_catalog_pack_id", table_name="signal_catalog")
        op.drop_index("ix_signal_catalog_domain", table_name="signal_catalog")
        op.drop_table("signal_catalog")
    if _table_exists(conn, "tasks") and _index_exists(conn, "tasks", "ix_tasks_tenant_opportunity"):
        op.drop_index("ix_tasks_tenant_opportunity", table_name="tasks")
    if _table_exists(conn, "tasks") and _column_exists(conn, "tasks", "opportunity_id"):
        op.drop_column("tasks", "opportunity_id")
