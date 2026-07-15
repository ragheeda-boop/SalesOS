"""Add failed_attempts and locked_until columns to users table

These columns are required by the identity service for account lockout logic.

Revision ID: 0033
Revises: 0032
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0033"
down_revision: Union[str, None] = "0032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "failed_attempts" not in columns:
        op.add_column("users", sa.Column("failed_attempts", sa.Integer, nullable=False, server_default="0"))

    if "locked_until" not in columns:
        op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "locked_until" in columns:
        op.drop_column("users", "locked_until")

    if "failed_attempts" in columns:
        op.drop_column("users", "failed_attempts")
