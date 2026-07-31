"""analytics_schema_reconciliation

Revision ID: 07e3ec4084fc
Revises: 0afbf3e6ae53
Create Date: 2026-07-31 17:38:31.197134
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '07e3ec4084fc'
down_revision: Union[str, None] = '0afbf3e6ae53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analytics_reports", sa.Column("metrics", postgresql.JSON, nullable=False, server_default="[]"))
    op.add_column("analytics_reports", sa.Column("dimensions", postgresql.JSON, nullable=False, server_default="[]"))
    op.add_column("analytics_reports", sa.Column("filters", postgresql.JSON, nullable=False, server_default="{}"))
    op.add_column("analytics_reports", sa.Column("visualization_type", sa.String(50), nullable=False, server_default="table"))
    op.add_column("analytics_reports", sa.Column("created_by", sa.String(36), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("analytics_reports", "created_by")
    op.drop_column("analytics_reports", "visualization_type")
    op.drop_column("analytics_reports", "filters")
    op.drop_column("analytics_reports", "dimensions")
    op.drop_column("analytics_reports", "metrics")
