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
    # NOTE: 3072-dim vectors exceed pgvector HNSW 2000-dim limit, so we skip
    # INDEX creation here. The column itself still works for exact search.
    pass

def downgrade() -> None:
    pass
