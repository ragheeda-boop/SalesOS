"""STORY-05-02: Stripe webhook idempotency ledger + subscription Stripe ids.

Revision ID: e5c1f34a6b02
Revises: d4b0e23f5a91
Create Date: 2026-08-02

Additive only. No RLS. No DEC-085. No secrets in migration.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e5c1f34a6b02"
down_revision: Union[str, None] = "d4b0e23f5a91"
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
    if _table_exists(conn, "subscriptions"):
        if not _column_exists(conn, "subscriptions", "stripe_customer_id"):
            op.add_column(
                "subscriptions",
                sa.Column("stripe_customer_id", sa.String(128), nullable=True),
            )
        if not _column_exists(conn, "subscriptions", "stripe_subscription_id"):
            op.add_column(
                "subscriptions",
                sa.Column("stripe_subscription_id", sa.String(128), nullable=True),
            )
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_customer_id "
                "ON subscriptions (stripe_customer_id)"
            )
        )
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_subscription_id "
                "ON subscriptions (stripe_subscription_id)"
            )
        )

    if not _table_exists(conn, "stripe_webhook_events"):
        op.create_table(
            "stripe_webhook_events",
            sa.Column("event_id", sa.String(128), primary_key=True),
            sa.Column("event_type", sa.String(128), nullable=False),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("result", sa.String(64), nullable=False, server_default="processed"),
            sa.Column(
                "processed_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_stripe_webhook_events_type",
            "stripe_webhook_events",
            ["event_type"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "stripe_webhook_events"):
        op.drop_index("ix_stripe_webhook_events_type", table_name="stripe_webhook_events")
        op.drop_table("stripe_webhook_events")
    if _table_exists(conn, "subscriptions"):
        op.execute(sa.text("DROP INDEX IF EXISTS ix_subscriptions_stripe_subscription_id"))
        op.execute(sa.text("DROP INDEX IF EXISTS ix_subscriptions_stripe_customer_id"))
        if _column_exists(conn, "subscriptions", "stripe_subscription_id"):
            op.drop_column("subscriptions", "stripe_subscription_id")
        if _column_exists(conn, "subscriptions", "stripe_customer_id"):
            op.drop_column("subscriptions", "stripe_customer_id")
