"""analytics tables for Report Definitions and Report Executions

Creates:
  - analytics_reports — saved report definitions with schedule and config
  - analytics_report_executions — execution history for each report

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analytics_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, server_default="custom"),
        sa.Column("config", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("schedule", sa.String(100), nullable=False, server_default="one-time"),
        sa.Column("recipients", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "analytics_report_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("output_format", sa.String(10), nullable=False, server_default="json"),
        sa.Column("output_path", sa.String(1000), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analytics_executions_report", "analytics_report_executions", ["report_id"])


def downgrade() -> None:
    op.drop_table("analytics_report_executions")
    op.drop_table("analytics_reports")
