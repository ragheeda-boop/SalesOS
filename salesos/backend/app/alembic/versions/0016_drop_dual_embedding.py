"""companies: drop duplicate embedding ARRAY column, keep embedding_vector

The companies table has both `embedding ARRAY(Float)` (from 0006) and
`embedding_vector vector(3072)` (added by ALTER in 0006). This migration
removes the generic ARRAY column since the native pgvector column is
the canonical storage for embeddings.

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("companies", "embedding")


def downgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
    )
