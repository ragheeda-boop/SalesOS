"""Add RLS to 3 Phase 3/4 AI Foundation tables missing tenant isolation.

Tables: approval_requests, llm_cost_entries, tenant_llm_budgets

All three have tenant_id columns but were created after the bulk RLS rollouts
and were never added to ALL_TENANT_TABLES in rls.py.

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m8
Create Date: 2026-08-24
"""
from alembic import op

revision = "i3j4k5l6m7n8"
down_revision = "h2i3j4k5l6m8"
branch_labels = None
depends_on = None

TABLES = ["approval_requests", "llm_cost_entries", "tenant_llm_budgets"]


def upgrade() -> None:
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
