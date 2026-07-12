"""companies: add HNSW index on embedding_vector for ANN search

pgvector 0.6+ supports HNSW up to 16000 dimensions, so our 3072d
embedding is well within limits. This enables fast approximate nearest
neighbor search on companies.

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_embedding_hnsw
        ON companies
        USING hnsw (embedding_vector vector_cosine_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_companies_embedding_hnsw")
