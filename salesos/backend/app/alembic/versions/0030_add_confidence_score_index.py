"""Add confidence_score DESC index on companies table

Adds a B-tree index on companies.confidence_score DESC to optimize
sorting queries that order by confidence_score. Without this index,
queries like "SELECT * FROM companies ORDER BY confidence_score DESC"
perform full-table sorts.

Identified by performance audit: p95 8s for enrichment (confidence-based scoring)

Revision ID: 0030
Revises: 0029
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0030"
down_revision: Union[str, None] = "0029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_companies_confidence_score", "companies",
        ["confidence_score"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_companies_confidence_score")
