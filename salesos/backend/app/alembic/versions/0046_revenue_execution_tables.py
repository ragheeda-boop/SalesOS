"""Create revenue_execution opportunities and tasks tables.

Revision ID: 0046
Revises: 0045
Create Date: 2026-07-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0046"
down_revision: Union[str, None] = "0045"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("stage", sa.String(20), server_default="identified"),
        sa.Column("estimated_value", sa.Numeric(15, 2), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("win_probability", sa.Numeric(3, 2), nullable=True),
        sa.Column("source", sa.String(20), server_default="manual"),
        sa.Column("source_action_id", sa.String(100), nullable=True),
        sa.Column("buying_intent", sa.Numeric(3, 2), nullable=True),
        sa.Column("relationship_strength", sa.Numeric(3, 2), nullable=True),
        sa.Column("risk_level", sa.String(10), nullable=True),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("stage_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rev_opportunities_tenant_id", "opportunities", ["tenant_id"])
    op.create_index("ix_rev_opportunities_tenant_stage", "opportunities", ["tenant_id", "stage"])
    op.create_index("ix_rev_opportunities_company", "opportunities", ["company_id"])

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("priority", sa.String(10), nullable=True),
        sa.Column("source", sa.String(20), server_default="manual"),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rev_tasks_tenant_id", "tasks", ["tenant_id"])
    op.create_index("ix_rev_tasks_tenant_priority", "tasks", ["tenant_id", "priority"])
    op.create_index("ix_rev_tasks_assignee_completed", "tasks", ["assignee_id", "completed"])


def downgrade() -> None:
    op.drop_index("ix_rev_tasks_assignee_completed", table_name="tasks")
    op.drop_index("ix_rev_tasks_tenant_priority", table_name="tasks")
    op.drop_index("ix_rev_tasks_tenant_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_rev_opportunities_company", table_name="opportunities")
    op.drop_index("ix_rev_opportunities_tenant_stage", table_name="opportunities")
    op.drop_index("ix_rev_opportunities_tenant_id", table_name="opportunities")
    op.drop_table("opportunities")
