"""create_agent_tasks

Revision ID: f4aee055fd6e
Revises: f7a1b82c3d09
Create Date: 2026-08-09 01:43:48.016061

Agent Runtime Phase 1: core tables for durable agent execution.
  - agent_tasks: lease-based work queue with fencing token
  - agent_runs: execution sessions with budget/cost tracking
  - agent_actions: side-effect ledger with idempotency

All tables have FORCE ROW LEVEL SECURITY with fail-closed semantics.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = 'f4aee055fd6e'
down_revision: Union[str, None] = 'f7a1b82c3d09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AGENT_TABLES = ("agent_tasks", "agent_runs", "agent_actions")


def _rls_sql(table: str) -> list[str]:
    return [
        f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY',
        f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY',
        f'CREATE POLICY tenant_isolation ON "{table}" FOR ALL '
        f'USING (tenant_id::text = current_setting(\'app.tenant_id\', true)) '
        f'WITH CHECK (tenant_id::text = current_setting(\'app.tenant_id\', true))',
    ]


def upgrade() -> None:
    # --- agent_tasks ---
    op.create_table(
        "agent_tasks",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", PG_UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),

        sa.Column("kind", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", PG_UUID(as_uuid=True)),

        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("completion_reason", sa.String(30)),

        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("due_at", sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.Column("budget", sa.Integer(), server_default="4"),
        sa.Column("max_attempts", sa.Integer(), server_default="3"),
        sa.Column("attempts", sa.Integer(), server_default="0"),

        sa.Column("lease_generation", sa.Integer(), server_default="0"),
        sa.Column("leased_until", sa.DateTime(timezone=True)),
        sa.Column("leased_by", sa.String(100)),

        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("outcome", sa.Text()),
        sa.Column("session_id", sa.String(255)),

        sa.Column("input_data", sa.JSON(), server_default="{}"),
        sa.Column("idempotency_key", sa.String(255)),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_agent_tasks_dispatch", "agent_tasks",
                    ["tenant_id", "status", "due_at"],
                    postgresql_where=sa.text("status = 'PENDING'"))
    op.create_index("idx_agent_tasks_lease", "agent_tasks",
                    ["tenant_id", "status", "leased_until"],
                    postgresql_where=sa.text("status IN ('CLAIMED', 'RUNNING')"))
    op.create_index("idx_agent_tasks_entity", "agent_tasks",
                    ["tenant_id", "entity_type", "entity_id", "kind"])
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_agent_tasks_idempotency ON agent_tasks "
        "(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
    ))

    # --- agent_runs ---
    op.create_table(
        "agent_runs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("task_id", PG_UUID(as_uuid=True), sa.ForeignKey("agent_tasks.id"), nullable=False),
        sa.Column("tenant_id", PG_UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),

        sa.Column("agent_type", sa.String(100), nullable=False),

        sa.Column("status", sa.String(20), server_default="RUNNING"),

        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),

        sa.Column("budget_spent", sa.Integer(), server_default="0"),
        sa.Column("input_tokens", sa.BigInteger(), server_default="0"),
        sa.Column("output_tokens", sa.BigInteger(), server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), server_default="0"),

        sa.Column("result_summary", sa.Text()),
        sa.Column("result_data", sa.JSON(), server_default="{}"),
        sa.Column("session_data", sa.JSON(), server_default="{}"),
    )
    op.create_index("idx_agent_runs_task", "agent_runs", ["task_id"])
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_agent_runs_active ON agent_runs "
        "(task_id) WHERE status = 'RUNNING'"
    ))

    # --- agent_actions ---
    op.create_table(
        "agent_actions",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", PG_UUID(as_uuid=True), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("task_id", PG_UUID(as_uuid=True), sa.ForeignKey("agent_tasks.id"), nullable=False),
        sa.Column("tenant_id", PG_UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),

        sa.Column("action_type", sa.String(20), nullable=False),
        sa.Column("target_entity", sa.String(100), nullable=False),
        sa.Column("target_id", PG_UUID(as_uuid=True)),
        sa.Column("payload", sa.JSON(), server_default="{}"),

        sa.Column("status", sa.String(20), server_default="PENDING"),
        sa.Column("idempotency_key", sa.String(255)),
        sa.Column("pdp_result", sa.String(20)),
        sa.Column("approval_id", PG_UUID(as_uuid=True)),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
    )
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_agent_actions_idempotency ON agent_actions "
        "(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
    ))

    # --- RLS on all agent tables ---
    for table in AGENT_TABLES:
        for stmt in _rls_sql(table):
            op.execute(sa.text(stmt))


def downgrade() -> None:
    for table in reversed(AGENT_TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"'))
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
    op.drop_table("agent_actions")
    op.drop_table("agent_runs")
    op.drop_table("agent_tasks")
