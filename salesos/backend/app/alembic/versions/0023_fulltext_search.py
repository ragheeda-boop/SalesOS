"""fulltext search: add search_vector generated column + GIN index

BUG-001 fix — Adds a deterministic, index-backed search_vector column
that uses GENERATED ALWAYS AS (no trigger needed). The existing tsv
column (0006) uses a trigger; this column is purely declarative and
indexed with GIN for fast full-text queries.

Creates:
  - companies.search_vector (tsvector, GENERATED ALWAYS AS ... STORED)
  - GIN index on search_vector for fast @@ matching
  - Adds region, legal_form, activity_description to tsvector for
    richer full-text queries

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add search_vector as a GENERATED ALWAYS column — no trigger needed.
    # Includes name_ar, name_en, cr_number, city, industry, activity_description,
    # region, and legal_form for comprehensive full-text coverage.
    op.execute("""
        ALTER TABLE companies
        ADD COLUMN IF NOT EXISTS search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('simple',
                COALESCE(name_ar, '') || ' ' ||
                COALESCE(name_en, '') || ' ' ||
                COALESCE(cr_number, '') || ' ' ||
                COALESCE(city, '') || ' ' ||
                COALESCE(industry, '') || ' ' ||
                COALESCE(activity_description, '') || ' ' ||
                COALESCE(region, '') || ' ' ||
                COALESCE(legal_form, '')
            )
        ) STORED
    """)

    # GIN index for fast full-text search — critical for 100K+ rows.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_search_vector
        ON companies USING GIN(search_vector)
    """)

    # Populate the existing tsv column from search_vector data (backfill)
    # so both paths (tsv trigger and search_vector) stay in sync.
    op.execute("""
        UPDATE companies SET tsv = search_vector
        WHERE tsv IS NULL OR tsv != search_vector
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_companies_search_vector")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS search_vector")
