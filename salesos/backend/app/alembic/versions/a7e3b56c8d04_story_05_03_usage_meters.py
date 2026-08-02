"""STORY-05-03: usage_meter_events + usage_meters (OBJ-324).

Revision ID: a7e3b56c8d04
Revises: f6d2a45b7c03
Create Date: 2026-08-02

Additive Owner-plane tables. No RLS. No DEC-085. No secrets.
Hourly rollup substrate — events append, meters aggregate.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7e3b56c8d04"
down_revision: Union[str, None] = "f6d2a45b7c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "usage_meter_events"):
        op.create_table(
            "usage_meter_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("metric_key", sa.String(64), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
            sa.Column("op", sa.String(8), nullable=False, server_default="add"),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("rolled_up_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source", sa.String(64), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_usage_meter_events_tenant_metric",
            "usage_meter_events",
            ["tenant_id", "metric_key"],
        )
        op.create_index(
            "ix_usage_meter_events_pending",
            "usage_meter_events",
            ["rolled_up_at", "recorded_at"],
        )

    if not _table_exists(conn, "usage_meters"):
        op.create_table(
            "usage_meters",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("metric_key", sa.String(64), nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
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
            sa.UniqueConstraint(
                "tenant_id",
                "metric_key",
                "period_start",
                name="uq_usage_meters_tenant_metric_period",
            ),
        )
        op.create_index("ix_usage_meters_tenant_id", "usage_meters", ["tenant_id"])
        op.create_index(
            "ix_usage_meters_metric_period",
            "usage_meters",
            ["metric_key", "period_start"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "usage_meters"):
        op.drop_index("ix_usage_meters_metric_period", table_name="usage_meters")
        op.drop_index("ix_usage_meters_tenant_id", table_name="usage_meters")
        op.drop_table("usage_meters")
    if _table_exists(conn, "usage_meter_events"):
        op.drop_index("ix_usage_meter_events_pending", table_name="usage_meter_events")
        op.drop_index("ix_usage_meter_events_tenant_metric", table_name="usage_meter_events")
        op.drop_table("usage_meter_events")
