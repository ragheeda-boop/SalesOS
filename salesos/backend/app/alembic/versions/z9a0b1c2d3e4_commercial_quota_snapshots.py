"""Persist tenant-isolated commercial quota snapshots.

Revision ID: z9a0b1c2d3e4
Revises: y8z9a0b1c2d3
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.alembic.lib.rls import generate_policy_sql


revision: str = "z9a0b1c2d3e4"
down_revision: str | None = "y8z9a0b1c2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Quotas and territories pre-date the RLS migration framework. Bring their
    # existing tenant_id contracts under the same forced policy before adding
    # historical quota state that depends on them.
    for table in ("commercial_quotas", "commercial_territories", "commercial_reviews"):
        for statement in generate_policy_sql(table).strip().split(";\n"):
            if statement.strip():
                op.execute(sa.text(statement.strip()))
        op.execute(sa.text(f"REVOKE ALL ON {table} FROM PUBLIC"))
        op.execute(
            sa.text(
                "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') "
                f"THEN GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO salesos_app; "
                "END IF; END $grant$;"
            )
        )

    op.create_table(
        "commercial_quota_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("period_label", sa.String(100), nullable=False, server_default=""),
        sa.Column("quotas", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("team", sa.JSON(), nullable=True),
        sa.Column("total_target", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_attained", sa.Float(), nullable=False, server_default="0"),
        sa.Column("overall_attainment", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_commercial_quota_snapshots_tenant_created",
        "commercial_quota_snapshots",
        ["tenant_id", "created_at"],
    )
    for statement in generate_policy_sql("commercial_quota_snapshots").strip().split(";\n"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))
    op.execute(sa.text("REVOKE ALL ON commercial_quota_snapshots FROM PUBLIC"))
    op.execute(
        sa.text(
            "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') "
            "THEN GRANT SELECT, INSERT ON commercial_quota_snapshots TO salesos_app; "
            "END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.execute(sa.text('DROP POLICY IF EXISTS "tenant_isolation_commercial_quota_snapshots" ON "commercial_quota_snapshots"'))
    op.execute(sa.text('ALTER TABLE "commercial_quota_snapshots" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "commercial_quota_snapshots" DISABLE ROW LEVEL SECURITY'))
    op.drop_index("ix_commercial_quota_snapshots_tenant_created", table_name="commercial_quota_snapshots")
    op.drop_table("commercial_quota_snapshots")
    for table in ("commercial_reviews", "commercial_territories", "commercial_quotas"):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"'))
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
