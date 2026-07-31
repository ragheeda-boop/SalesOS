"""add_missing_registered_model_tables

Revision ID: 77214759646c
Revises: 0052
Create Date: 2026-07-31 13:46:01.984206
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '77214759646c'
down_revision: Union[str, None] = '0052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analytics_report_shares",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("report_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("permission", sa.String(20), nullable=False, server_default="view"),
        sa.Column("shared_by", sa.String(36), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analytics_report_shares_report_id"), "analytics_report_shares", ["report_id"])
    op.create_index(op.f("ix_analytics_report_shares_user_id"), "analytics_report_shares", ["user_id"])

    op.create_table(
        "analytics_scheduled_reports",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("report_id", sa.String(36), nullable=False),
        sa.Column("cadence", sa.String(20), nullable=False, server_default="weekly"),
        sa.Column("recipients", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("next_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analytics_scheduled_reports_report_id"), "analytics_scheduled_reports", ["report_id"])
    op.create_index(op.f("ix_analytics_scheduled_reports_tenant_id"), "analytics_scheduled_reports", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_analytics_scheduled_reports_tenant_id"), table_name="analytics_scheduled_reports")
    op.drop_index(op.f("ix_analytics_scheduled_reports_report_id"), table_name="analytics_scheduled_reports")
    op.drop_table("analytics_scheduled_reports")
    op.drop_index(op.f("ix_analytics_report_shares_user_id"), table_name="analytics_report_shares")
    op.drop_index(op.f("ix_analytics_report_shares_report_id"), table_name="analytics_report_shares")
    op.drop_table("analytics_report_shares")
