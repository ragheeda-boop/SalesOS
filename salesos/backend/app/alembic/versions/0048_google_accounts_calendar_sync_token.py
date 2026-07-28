"""Add calendar_sync_token to google_accounts for incremental Calendar sync.

Revision ID: 0048
Revises: 0047
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0048"
down_revision: Union[str, None] = "0047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "google_accounts",
        sa.Column("calendar_sync_token", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("google_accounts", "calendar_sync_token")
