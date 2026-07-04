"""vector store: create vectors table for PgVectorStore

Creates:
  - vectors — generic vector collection table for PgVectorStore (semantic search)

Revision ID: 0010
Revises: 0009
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vectors",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_vectors_created_at", "vectors", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_vectors_created_at", table_name="vectors")
    op.drop_table("vectors")
