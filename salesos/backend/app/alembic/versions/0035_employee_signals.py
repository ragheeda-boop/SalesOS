"""Create employee_signals and employee_scores tables

Revision ID: 0035
Revises: 0034
Create Date: 2026-07-16

Idempotent: skips tables/indexes that already exist.
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0035"
down_revision: str | None = "0034"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def _index_exists(conn, table: str, index_name: str) -> bool:
    inspector = sa.inspect(conn)
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "employee_signals"):
        op.create_table(
            "employee_signals",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("signal_type", sa.String(50), nullable=False),
            sa.Column("source", sa.String(30), nullable=False),
            sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    for name, cols in (
        ("ix_employee_signals_tenant_employee", ["tenant_id", "employee_id"]),
        ("ix_employee_signals_source", ["source"]),
        ("ix_employee_signals_type", ["signal_type"]),
        ("ix_employee_signals_timestamp", ["timestamp"]),
    ):
        if _table_exists(conn, "employee_signals") and not _index_exists(conn, "employee_signals", name):
            op.create_index(name, "employee_signals", cols)

    if not _table_exists(conn, "employee_scores"):
        op.create_table(
            "employee_scores",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("overall_score", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("signal_volume_score", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("recency_score", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("diversity_score", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("completion_rate", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("confidence_interval_low", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("confidence_interval_high", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("signal_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    if _table_exists(conn, "employee_scores") and not _index_exists(
        conn, "employee_scores", "ix_employee_scores_tenant_employee"
    ):
        op.create_index(
            "ix_employee_scores_tenant_employee",
            "employee_scores",
            ["tenant_id", "employee_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "employee_scores"):
        op.drop_table("employee_scores")
    if _table_exists(conn, "employee_signals"):
        op.drop_table("employee_signals")
