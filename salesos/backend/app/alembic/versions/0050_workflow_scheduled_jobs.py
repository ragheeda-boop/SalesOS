"""Add scheduled_jobs, job_executions, and workflow timeout column

Creates:
  - scheduled_jobs — cron/interval/one-time scheduled workflow jobs
  - job_executions — execution history for each scheduled job
  - timeout_seconds column on workflow_definitions

Revision ID: 0050
Revises: 0049
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0050"
down_revision: Union[str, None] = "0049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Add timeout_seconds column to workflow_definitions
    has_timeout = any(
        col["name"] == "timeout_seconds"
        for col in inspector.get_columns("workflow_definitions")
    )
    if not has_timeout:
        op.add_column(
            "workflow_definitions",
            sa.Column("timeout_seconds", sa.Float(), nullable=True),
        )

    # scheduled_jobs table
    if "scheduled_jobs" not in inspector.get_table_names():
        op.create_table(
            "scheduled_jobs",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(64), nullable=False),
            sa.Column("job_type", sa.String(20), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("config", JSONB, server_default="{}"),
            sa.Column("schedule", sa.String(255), server_default=""),
            sa.Column("status", sa.String(20), server_default="active"),
            sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("run_count", sa.Integer(), server_default="0"),
            sa.Column("max_retries", sa.Integer(), server_default="3"),
            sa.Column("retry_count", sa.Integer(), server_default="0"),
            sa.Column("payload", JSONB, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_scheduled_jobs_tenant_id", "scheduled_jobs", ["tenant_id"])
        op.create_index("ix_scheduled_jobs_status", "scheduled_jobs", ["status"])
        op.create_index("ix_scheduled_jobs_next_run", "scheduled_jobs", ["next_run_at"])

    # job_executions table
    if "job_executions" not in inspector.get_table_names():
        op.create_table(
            "job_executions",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("job_id", sa.String(64), nullable=False),
            sa.Column("tenant_id", sa.String(64), nullable=False),
            sa.Column("status", sa.String(20), server_default="pending"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("result", JSONB, nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
        )
        op.create_index("ix_job_executions_job_id", "job_executions", ["job_id"])
        op.create_index("ix_job_executions_tenant_id", "job_executions", ["tenant_id"])
        op.create_index("ix_job_executions_status", "job_executions", ["status"])


def downgrade() -> None:
    op.drop_table("job_executions")
    op.drop_table("scheduled_jobs")
    op.drop_column("workflow_definitions", "timeout_seconds")
