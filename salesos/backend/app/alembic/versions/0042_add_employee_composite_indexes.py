"""Add composite indexes for employee_signals and employee_scores

Revision ID: 0042
Revises: 0041
Create Date: 2026-07-25

Optimizes most-common query patterns:
  - employee_signals: (tenant_id, employee_id, timestamp) for filtered timeline
  - employee_scores: (tenant_id, employee_id, generated_at) for latest-score lookups

Idempotent: skips indexes that already exist.
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0042"
down_revision: str | None = "0041"
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

    if _table_exists(conn, "employee_signals") and not _index_exists(
        conn, "employee_signals", "ix_employee_signals_tenant_employee_ts"
    ):
        op.create_index(
            "ix_employee_signals_tenant_employee_ts",
            "employee_signals",
            ["tenant_id", "employee_id", "timestamp"],
        )

    if _table_exists(conn, "employee_scores") and not _index_exists(
        conn, "employee_scores", "ix_employee_scores_tenant_employee_gen"
    ):
        op.create_index(
            "ix_employee_scores_tenant_employee_gen",
            "employee_scores",
            ["tenant_id", "employee_id", "generated_at"],
        )


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "employee_signals") and _index_exists(
        conn, "employee_signals", "ix_employee_signals_tenant_employee_ts"
    ):
        op.drop_index(
            "ix_employee_signals_tenant_employee_ts",
            table_name="employee_signals",
        )

    if _table_exists(conn, "employee_scores") and _index_exists(
        conn, "employee_scores", "ix_employee_scores_tenant_employee_gen"
    ):
        op.drop_index(
            "ix_employee_scores_tenant_employee_gen",
            table_name="employee_scores",
        )
