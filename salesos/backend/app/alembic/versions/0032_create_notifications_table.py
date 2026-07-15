"""Create notifications table

Creates:
  - notifications — persistent notifications per user per tenant

Revision ID: 0032
Revises: 0031
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0032"
down_revision: Union[str, None] = "0031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "notifications" not in inspector.get_table_names():
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("notification_id", sa.String(64), nullable=False, unique=True, index=True),
            sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
            sa.Column("user_id", sa.String(64), nullable=False, index=True),
            sa.Column("type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("body", sa.Text, server_default=""),
            sa.Column("data", postgresql.JSONB, nullable=True, server_default="{}"),
            sa.Column("read", sa.Boolean, server_default="false", index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        )
        op.create_index("ix_notifications_tenant_user", "notifications", ["tenant_id", "user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
