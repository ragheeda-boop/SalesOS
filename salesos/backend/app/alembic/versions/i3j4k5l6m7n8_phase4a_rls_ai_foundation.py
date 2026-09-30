"""Add RLS to 3 Phase 3/4 AI Foundation tables missing tenant isolation.

Tables: approval_requests, llm_cost_entries, tenant_llm_budgets

All three have tenant_id columns but were created after the bulk RLS rollouts
and were never added to ALL_TENANT_TABLES in rls.py.

Staging (2026-09-30) was stamped at h2i3j4k5l6m8 while these relations were
absent, so ENABLE ROW LEVEL SECURITY failed and the pre-deploy aborted.
A clean chain creates them in f6/f8 before this revision; this upgrade also
creates them when a drifted stamp skipped that DDL. DDL matches those files.

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m8
Create Date: 2026-08-24
"""
import sqlalchemy as sa
from alembic import op

revision = "i3j4k5l6m7n8"
down_revision = "h2i3j4k5l6m8"
branch_labels = None
depends_on = None

TABLES = ["approval_requests", "llm_cost_entries", "tenant_llm_budgets"]


def _relation_exists(name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text("SELECT to_regclass(:qualified) IS NOT NULL"),
            {"qualified": f"public.{name}"},
        ).scalar()
    )


def _ensure_foundation_tables() -> None:
    """Create the f6/f8 tables when a drifted stamp never did."""
    if not _relation_exists("approval_requests"):
        op.create_table(
            "approval_requests",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("target_type", sa.String(50), nullable=False, index=True),
            sa.Column("target_id", sa.String(36), nullable=False, index=True),
            sa.Column("requested_by", sa.String(36), server_default="system"),
            sa.Column("action_summary", sa.Text(), server_default=""),
            sa.Column("action_evidence", sa.JSON(), server_default="[]"),
            sa.Column("required_level", sa.String(20), server_default="manager"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
            sa.Column("assigned_to", sa.String(36), server_default=""),
            sa.Column("decisions", sa.JSON(), server_default="[]"),
            sa.Column("metadata", sa.JSON(), server_default="{}"),
            sa.Column("priority", sa.Float(), server_default="5.0"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "ix_approval_requests_tenant_status",
            "approval_requests",
            ["tenant_id", "status"],
        )
        op.create_index(
            "ix_approval_requests_tenant_target",
            "approval_requests",
            ["tenant_id", "target_type", "target_id"],
        )
        op.create_index(
            "ix_approval_requests_assigned",
            "approval_requests",
            ["tenant_id", "assigned_to", "status"],
        )

    if not _relation_exists("llm_cost_entries"):
        op.create_table(
            "llm_cost_entries",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
            sa.Column("user_id", sa.String(64), nullable=True),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("model", sa.String(128), nullable=False),
            sa.Column("operation", sa.String(32), nullable=False, server_default="completion"),
            sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cost", sa.Numeric(12, 8), nullable=False, server_default="0"),
            sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("error", sa.String(256), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "timestamp",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_llm_cost_entries_tenant_ts",
            "llm_cost_entries",
            ["tenant_id", "timestamp"],
        )
        op.create_index("ix_llm_cost_entries_provider", "llm_cost_entries", ["provider"])
        op.create_index("ix_llm_cost_entries_model", "llm_cost_entries", ["model"])

    if not _relation_exists("tenant_llm_budgets"):
        op.create_table(
            "tenant_llm_budgets",
            sa.Column("tenant_id", sa.String(64), primary_key=True),
            sa.Column("monthly_budget_cents", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column(
                "period_start",
                sa.Date(),
                nullable=False,
                server_default=sa.text("date_trunc('month', now())::date"),
            ),
            sa.Column("period_spend_cents", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("is_enforced", sa.Boolean(), nullable=False, server_default=sa.false()),
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


def upgrade() -> None:
    _ensure_foundation_tables()
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"'
        )
        op.execute(
            f'CREATE POLICY "tenant_isolation_{table}" ON "{table}" '
            f"FOR ALL "
            f"USING (tenant_id::text = current_setting('app.tenant_id', true)) "
            f"WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
