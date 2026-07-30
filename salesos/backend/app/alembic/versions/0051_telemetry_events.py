"""Create telemetry_events table

Revision ID: 0051
Revises: 0050
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0051"
down_revision: Union[str, None] = "0050"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "telemetry_events" not in inspector.get_table_names():
        op.create_table(
            "telemetry_events",
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
            sa.Column("user_id", sa.String(64), nullable=False, index=True),
            sa.Column("event_type", sa.String(100), nullable=False, index=True),
            sa.Column("properties", JSONB, nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("telemetry_events")
