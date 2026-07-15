"""Create workflow_definitions and workflow_executions tables

Creates:
  - workflow_definitions — stored workflow definitions per tenant
  - workflow_executions — execution history for each workflow

Revision ID: 0031
Revises: 0030
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0031"
down_revision: Union[str, None] = "0030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "workflow_definitions" not in inspector.get_table_names():
        op.create_table(
            "workflow_definitions",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text, server_default=""),
            sa.Column("trigger_type", sa.String(50), server_default="manual"),
            sa.Column("status", sa.String(20), server_default="draft", index=True),
            sa.Column("steps", postgresql.JSONB, server_default="[]"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_workflow_definitions_tenant", "workflow_definitions", ["tenant_id"])

    if "workflow_executions" not in inspector.get_table_names():
        op.create_table(
            "workflow_executions",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("workflow_id", sa.String(64), nullable=False, index=True),
            sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
            sa.Column("trigger_event", sa.String(100), server_default="manual"),
            sa.Column("status", sa.String(20), server_default="running", index=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error", sa.Text, nullable=True),
            sa.Column("step_results", postgresql.JSONB, server_default="[]"),
        )
        op.create_index("ix_workflow_executions_tenant", "workflow_executions", ["tenant_id"])
        op.create_index("ix_workflow_executions_workflow", "workflow_executions", ["workflow_id"])


def downgrade() -> None:
    op.drop_table("workflow_executions")
    op.drop_table("workflow_definitions")
