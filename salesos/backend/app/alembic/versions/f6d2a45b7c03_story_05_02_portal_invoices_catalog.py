"""STORY-05-02b: plan Stripe price ids + platform_billing_invoices.

Revision ID: f6d2a45b7c03
Revises: e5c1f34a6b02
Create Date: 2026-08-02

Additive only. No RLS. No DEC-085. No secrets in migration.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6d2a45b7c03"
down_revision: Union[str, None] = "e5c1f34a6b02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "admin_plans"):
        if not _column_exists(conn, "admin_plans", "stripe_price_id_monthly"):
            op.add_column(
                "admin_plans",
                sa.Column("stripe_price_id_monthly", sa.String(128), nullable=True),
            )
        if not _column_exists(conn, "admin_plans", "stripe_price_id_yearly"):
            op.add_column(
                "admin_plans",
                sa.Column("stripe_price_id_yearly", sa.String(128), nullable=True),
            )

    if not _table_exists(conn, "platform_billing_invoices"):
        op.create_table(
            "platform_billing_invoices",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("stripe_invoice_id", sa.String(128), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(10), nullable=False, server_default="SAR"),
            sa.Column("status", sa.String(32), nullable=False, server_default="open"),
            sa.Column("description", sa.String(2000), nullable=False, server_default=""),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("hosted_invoice_url", sa.String(1024), nullable=True),
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
            sa.UniqueConstraint("stripe_invoice_id", name="uq_platform_billing_invoices_stripe_id"),
        )
        op.create_index(
            "ix_platform_billing_invoices_tenant_id",
            "platform_billing_invoices",
            ["tenant_id"],
        )
        op.create_index(
            "ix_platform_billing_invoices_status",
            "platform_billing_invoices",
            ["status"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "platform_billing_invoices"):
        op.drop_index(
            "ix_platform_billing_invoices_status", table_name="platform_billing_invoices"
        )
        op.drop_index(
            "ix_platform_billing_invoices_tenant_id", table_name="platform_billing_invoices"
        )
        op.drop_table("platform_billing_invoices")
    if _table_exists(conn, "admin_plans"):
        if _column_exists(conn, "admin_plans", "stripe_price_id_yearly"):
            op.drop_column("admin_plans", "stripe_price_id_yearly")
        if _column_exists(conn, "admin_plans", "stripe_price_id_monthly"):
            op.drop_column("admin_plans", "stripe_price_id_monthly")
