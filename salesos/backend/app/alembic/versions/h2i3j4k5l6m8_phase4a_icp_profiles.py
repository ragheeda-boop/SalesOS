"""Phase 4A: persistent, tenant-scoped ICP profiles (canonical DEC-085 RLS).

Schema is derived 1:1 from app/modules/gtm/icp.ICPProfile (STORY-11-01):
criteria/weights are stored as JSONB matching ICPCriteria/ICPWeights.as_dict()
so the existing normalize/validate path stays the single source of truth.
Multiple active profiles per tenant are ALLOWED — the grounded ICP agent
evaluates every active profile and keeps the best fit_ratio.

Runtime consumption (sync MemICPStore vs async repository) is intentionally
NOT switched in this phase — see docs/adr/0109-icp-persistence.md
(DECISION REQUIRED section). Zero behavior change for the 13 agents.

Revision ID: h2i3j4k5l6m8
Revises: h1i2j3k4l5m7
Create Date: 2026-08-23
"""
import sqlalchemy as sa
from alembic import op

revision = "h2i3j4k5l6m8"
down_revision = "h1i2j3k4l5m7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "icp_profiles",
        sa.Column("id", sa.String(16), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
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
    op.create_index(
        "ix_icp_profiles_tenant_active",
        "icp_profiles",
        ["tenant_id", "is_active"],
    )
    op.execute("ALTER TABLE icp_profiles ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_icp_profiles ON icp_profiles "
        "USING ((tenant_id)::text = current_setting('app.tenant_id'::text, true)) "
        "WITH CHECK ((tenant_id)::text = current_setting('app.tenant_id'::text, true))"
    )
    op.execute("ALTER TABLE icp_profiles FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_icp_profiles ON icp_profiles")
    op.execute("ALTER TABLE icp_profiles NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE icp_profiles DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_icp_profiles_tenant_active", table_name="icp_profiles")
    op.drop_table("icp_profiles")
