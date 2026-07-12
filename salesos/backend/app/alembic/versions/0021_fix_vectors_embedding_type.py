"""fix vectors.embedding type from ARRAY(Float) to vector(3072)

The vectors table was created with postgresql.ARRAY(sa.Float()) for the
embedding column. This migration:
  1. Adds a new vector(3072) column
  2. Casts existing ARRAY data to vector type
  3. Drops the old ARRAY column
  4. Renames the new column to 'embedding'
  5. Creates an HNSW index for fast approximate nearest neighbor search

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new vector column
    op.execute("ALTER TABLE vectors ADD COLUMN embedding_vector vector(3072)")

    # Migrate existing data: cast ARRAY(Float) → vector(3072) via pgvector's array cast
    op.execute("""
        UPDATE vectors
        SET embedding_vector = embedding::vector(3072)
        WHERE embedding IS NOT NULL
    """)

    # Drop old ARRAY column
    op.drop_column("vectors", "embedding")

    # Rename new column to 'embedding'
    op.execute("ALTER TABLE vectors RENAME COLUMN embedding_vector TO embedding")

    # Make the new column NOT NULL (after data migration)
    op.execute("ALTER TABLE vectors ALTER COLUMN embedding SET NOT NULL")

    # Create HNSW index for approximate nearest neighbor search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vectors_embedding_hnsw
        ON vectors
        USING hnsw (embedding vector_cosine_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_vectors_embedding_hnsw")

    # Add back ARRAY column
    op.add_column(
        "vectors",
        sa.Column("embedding_old", postgresql.ARRAY(sa.Float()), nullable=True),
    )

    # Cast vector back to array
    op.execute("""
        UPDATE vectors
        SET embedding_old = embedding::float8[]
        WHERE embedding IS NOT NULL
    """)

    # Drop vector column
    op.drop_column("vectors", "embedding")

    # Rename old column back
    op.execute("ALTER TABLE vectors RENAME COLUMN embedding_old TO embedding")
