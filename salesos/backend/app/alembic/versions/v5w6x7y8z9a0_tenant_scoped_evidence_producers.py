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


def upgrade() -> None:
    op.add_column(
        "commercial_insights", sa.Column("idempotency_key", sa.String(128), nullable=True)
    )
    op.create_unique_constraint(
        "uq_commercial_insights_tenant_idempotency",
        "commercial_insights",
        ["tenant_id", "idempotency_key"],
    )

    op.add_column("commercial_evidence_items", sa.Column("tenant_id", sa.String(36), nullable=True))
    op.execute(
        "UPDATE commercial_evidence_items AS evidence "
        "SET tenant_id = insight.tenant_id "
        "FROM commercial_insights AS insight "
        "WHERE insight.id = evidence.insight_id AND evidence.tenant_id IS NULL"
    )

    op.execute("ALTER TABLE commercial_insights ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_commercial_insights "
        "ON commercial_insights FOR ALL "
        "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute("ALTER TABLE commercial_insights FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE commercial_evidence_items ENABLE ROW LEVEL SECURITY")
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
