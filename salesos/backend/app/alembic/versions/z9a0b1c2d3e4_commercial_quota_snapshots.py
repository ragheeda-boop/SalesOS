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


def _relation_exists(name: str) -> bool:
    return bool(
        op.get_bind()
        .execute(
            sa.text("SELECT to_regclass(:qualified) IS NOT NULL"),
            {"qualified": f"public.{name}"},
        )
        .scalar()
    )


def _ensure_quota_foundation() -> None:
    """Staging was stamped past the Phase 1 revisions that create these tables.

    d4e5f6a7b8c9 and b2c3d4e5f6a7 will not run again. Copy their DDL when the
    relations are absent, then apply this revision's row-security policy.
    """
    if not _relation_exists("commercial_quotas"):
        op.create_table(
            "commercial_quotas",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("rep_id", sa.String(36), nullable=False, index=True),
            sa.Column("rep_name", sa.String(200), nullable=True),
            sa.Column("period", sa.String(20), nullable=False, server_default="quarterly"),
            sa.Column("target_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
            sa.Column("attained_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_commercial_quotas_tenant_status", "commercial_quotas", ["tenant_id", "status"])
        op.create_index("ix_commercial_quotas_tenant_rep", "commercial_quotas", ["tenant_id", "rep_id"])
    if not _relation_exists("commercial_territories"):
        op.create_table(
            "commercial_territories",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("region", sa.String(200), nullable=True),
            sa.Column("rep_id", sa.String(36), nullable=True, index=True),
            sa.Column("rep_name", sa.String(200), nullable=True),
            sa.Column("account_ids", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index(
            "ix_commercial_territories_tenant_rep",
            "commercial_territories",
            ["tenant_id", "rep_id"],
        )
        op.create_index(
            "ix_commercial_territories_tenant_region",
            "commercial_territories",
            ["tenant_id", "region"],
        )
    if not _relation_exists("commercial_reviews"):
        op.create_table(
            "commercial_reviews",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("review_type", sa.String(50), nullable=False),
            sa.Column("target_id", sa.String(36), nullable=False, index=True),
            sa.Column("target_type", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("assigned_to", sa.String(36), nullable=True),
            sa.Column("requested_by", sa.String(36), nullable=True),
            sa.Column("decisions", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_commercial_reviews_tenant_status", "commercial_reviews", ["tenant_id", "status"])
        op.create_index("ix_commercial_reviews_target", "commercial_reviews", ["target_type", "target_id"])
        op.create_index("ix_commercial_reviews_assigned", "commercial_reviews", ["assigned_to"])


def upgrade() -> None:
    # Quotas, territories, and reviews pre-date the RLS migration framework.
    # A drifted stamp does not re-run their create revisions, so create them
    # when absent, then bring their tenant_id contracts under the forced policy.
    _ensure_quota_foundation()
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
