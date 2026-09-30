"""Add tenant-safe idempotent persistence for commercial evidence producers.

Revision ID: v5w6x7y8z9a0
Revises: u4v5w6x7y8z9
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "v5w6x7y8z9a0"
down_revision: str | None = "u4v5w6x7y8z9"
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


def _column_exists(table: str, column: str) -> bool:
    return bool(
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :table "
                "AND column_name = :column"
            ),
            {"table": table, "column": column},
        )
        .scalar()
    )


def upgrade() -> None:
    # Staging was stamped past e5f6a7b8c9d0 without these relations.
    # Create the original evidence tables when they are absent, including
    # the columns this revision adds, then continue with the normal alters.
    if not _relation_exists("commercial_insights"):
        op.create_table(
            "commercial_insights",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("category", sa.String(50), nullable=False, index=True),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("description", sa.Text(), server_default=""),
            sa.Column("target_id", sa.String(36), nullable=False, index=True),
            sa.Column("target_type", sa.String(50), nullable=False, index=True),
            sa.Column("overall_confidence", sa.Float(), server_default="0.0"),
            sa.Column("confidence_level", sa.String(20), server_default="unknown"),
            sa.Column("metadata", sa.JSON(), server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("idempotency_key", sa.String(128), nullable=True),
        )
        op.create_index(
            "ix_commercial_insights_tenant_category",
            "commercial_insights",
            ["tenant_id", "category"],
        )
        op.create_index(
            "ix_commercial_insights_tenant_confidence",
            "commercial_insights",
            ["tenant_id", "confidence_level"],
        )
    elif not _column_exists("commercial_insights", "idempotency_key"):
        op.add_column(
            "commercial_insights", sa.Column("idempotency_key", sa.String(128), nullable=True)
        )

    constraint_exists = op.get_bind().execute(
        sa.text(
            "SELECT 1 FROM pg_constraint "
            "WHERE conname = 'uq_commercial_insights_tenant_idempotency'"
        )
    ).scalar()
    if not constraint_exists:
        op.create_unique_constraint(
            "uq_commercial_insights_tenant_idempotency",
            "commercial_insights",
            ["tenant_id", "idempotency_key"],
        )

    if not _relation_exists("commercial_evidence_items"):
        op.create_table(
            "commercial_evidence_items",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("insight_id", sa.String(36), nullable=False, index=True),
            sa.Column("evidence_type", sa.String(50), nullable=False, index=True),
            sa.Column("source_domain", sa.String(50), nullable=False),
            sa.Column("source_type", sa.String(50), nullable=False),
            sa.Column("source_id", sa.String(36), server_default=""),
            sa.Column("source_name", sa.String(200), server_default=""),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("confidence", sa.Float(), server_default="0.0"),
            sa.Column("confidence_level", sa.String(20), server_default="unknown"),
            sa.Column("data", sa.JSON(), server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("tenant_id", sa.String(36), nullable=True),
        )
        op.create_index(
            "ix_commercial_evidence_insight", "commercial_evidence_items", ["insight_id"]
        )
        op.create_index(
            "ix_commercial_evidence_type", "commercial_evidence_items", ["evidence_type"]
        )
    elif not _column_exists("commercial_evidence_items", "tenant_id"):
        op.add_column(
            "commercial_evidence_items", sa.Column("tenant_id", sa.String(36), nullable=True)
        )
        op.execute(
            "UPDATE commercial_evidence_items AS evidence "
            "SET tenant_id = insight.tenant_id "
            "FROM commercial_insights AS insight "
            "WHERE insight.id = evidence.insight_id AND evidence.tenant_id IS NULL"
        )

    op.execute("ALTER TABLE commercial_insights ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_commercial_insights ON commercial_insights")
    op.execute(
        "CREATE POLICY tenant_isolation_commercial_insights "
        "ON commercial_insights FOR ALL "
        "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute("ALTER TABLE commercial_insights FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE commercial_evidence_items ENABLE ROW LEVEL SECURITY")
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_commercial_evidence_items "
        "ON commercial_evidence_items"
    )
    op.execute(
        "CREATE POLICY tenant_isolation_commercial_evidence_items "
        "ON commercial_evidence_items FOR ALL "
        "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute("ALTER TABLE commercial_evidence_items FORCE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON commercial_insights, commercial_evidence_items FROM PUBLIC")
    op.execute(
        sa.text(
            "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') "
            "THEN EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON commercial_insights, "
            "commercial_evidence_items TO salesos_app'; END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_commercial_evidence_items "
        "ON commercial_evidence_items"
    )
    op.execute("ALTER TABLE commercial_evidence_items NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE commercial_evidence_items DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_commercial_insights ON commercial_insights")
    op.execute("ALTER TABLE commercial_insights NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE commercial_insights DISABLE ROW LEVEL SECURITY")
    op.drop_column("commercial_evidence_items", "tenant_id")
    op.drop_constraint(
        "uq_commercial_insights_tenant_idempotency", "commercial_insights", type_="unique"
    )
    op.drop_column("commercial_insights", "idempotency_key")
