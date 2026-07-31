"""Add tenant_id column to decision_center_decisions

Revision ID: 0052
Revises: 0051
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0052"
down_revision: Union[str, None] = "0051"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "decision_center_decisions",
        sa.Column("tenant_id", sa.String(), nullable=True, index=True),
    )
    op.execute(
        "UPDATE decision_center_decisions SET tenant_id = decision_metadata->>'tenant_id'"
        " WHERE tenant_id IS NULL"
    )
    op.alter_column("decision_center_decisions", "tenant_id", nullable=False)

    op.add_column(
        "decision_center_templates",
        sa.Column("tenant_id", sa.String(), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_column("decision_center_templates", "tenant_id")
    op.drop_column("decision_center_decisions", "tenant_id")
