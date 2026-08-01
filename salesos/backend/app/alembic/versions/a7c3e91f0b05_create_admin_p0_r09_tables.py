"""DB-05 Slice 1: CREATE TABLE for admin P0 R-09 tables.

Revision ID: a7c3e91f0b05
Revises: 065d1d3a466b
Create Date: 2026-08-01

DEC-113 / DB-05 Slice 1 (admin cluster): additive CREATE only for
  - admin_licenses
  - admin_invoices
  - admin_transactions
  - admin_ai_costs
  - admin_jobs

Matches ORM in app/modules/admin/db_models.py.
Does NOT ENABLE RLS. Does NOT touch get_db() / DEC-085 set_config.
Idempotent: skip create when table already exists (init_db drift).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a7c3e91f0b05"
down_revision: Union[str, None] = "065d1d3a466b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "admin_licenses"):
        op.create_table(
            "admin_licenses",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
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
        )
        op.create_index("ix_admin_licenses_tenant_id", "admin_licenses", ["tenant_id"])
        op.create_index(
            "ix_admin_licenses_tenant_active",
            "admin_licenses",
            ["tenant_id", "is_active"],
        )

    if not _table_exists(conn, "admin_invoices"):
        op.create_table(
            "admin_invoices",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(10), nullable=False, server_default="SAR"),
            sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_admin_invoices_tenant_id", "admin_invoices", ["tenant_id"])
        op.create_index(
            "ix_admin_invoices_tenant_status",
            "admin_invoices",
            ["tenant_id", "status"],
        )
        op.create_index("ix_admin_invoices_due", "admin_invoices", ["due_date"])

    if not _table_exists(conn, "admin_transactions"):
        op.create_table(
            "admin_transactions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(10), nullable=False, server_default="SAR"),
            sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
            sa.Column("method", sa.String(50), nullable=False, server_default="card"),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("reference", sa.String(255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_admin_transactions_tenant_id", "admin_transactions", ["tenant_id"])
        op.create_index(
            "ix_admin_transactions_tenant_status",
            "admin_transactions",
            ["tenant_id", "status"],
        )

    if not _table_exists(conn, "admin_ai_costs"):
        op.create_table(
            "admin_ai_costs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("model", sa.String(100), nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("operation", sa.String(50), nullable=False, server_default="completion"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_admin_ai_costs_model", "admin_ai_costs", ["model"])
        op.create_index("ix_admin_ai_costs_tenant_id", "admin_ai_costs", ["tenant_id"])
        op.create_index(
            "ix_admin_ai_costs_tenant_model",
            "admin_ai_costs",
            ["tenant_id", "model"],
        )

    if not _table_exists(conn, "admin_jobs"):
        op.create_table(
            "admin_jobs",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("type", sa.String(100), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("tenant_id", sa.String(64), nullable=True),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column(
                "payload",
                postgresql.JSONB(),
                nullable=True,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column("result", postgresql.JSONB(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
            sa.Column(
                "logs",
                postgresql.JSONB(),
                nullable=True,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        )
        op.create_index("ix_admin_jobs_status", "admin_jobs", ["status"])
        op.create_index("ix_admin_jobs_tenant_id", "admin_jobs", ["tenant_id"])


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "admin_jobs"):
        op.drop_index("ix_admin_jobs_tenant_id", table_name="admin_jobs")
        op.drop_index("ix_admin_jobs_status", table_name="admin_jobs")
        op.drop_table("admin_jobs")
    if _table_exists(conn, "admin_ai_costs"):
        op.drop_index("ix_admin_ai_costs_tenant_model", table_name="admin_ai_costs")
        op.drop_index("ix_admin_ai_costs_tenant_id", table_name="admin_ai_costs")
        op.drop_index("ix_admin_ai_costs_model", table_name="admin_ai_costs")
        op.drop_table("admin_ai_costs")
    if _table_exists(conn, "admin_transactions"):
        op.drop_index("ix_admin_transactions_tenant_status", table_name="admin_transactions")
        op.drop_index("ix_admin_transactions_tenant_id", table_name="admin_transactions")
        op.drop_table("admin_transactions")
    if _table_exists(conn, "admin_invoices"):
        op.drop_index("ix_admin_invoices_due", table_name="admin_invoices")
        op.drop_index("ix_admin_invoices_tenant_status", table_name="admin_invoices")
        op.drop_index("ix_admin_invoices_tenant_id", table_name="admin_invoices")
        op.drop_table("admin_invoices")
    if _table_exists(conn, "admin_licenses"):
        op.drop_index("ix_admin_licenses_tenant_active", table_name="admin_licenses")
        op.drop_index("ix_admin_licenses_tenant_id", table_name="admin_licenses")
        op.drop_table("admin_licenses")
