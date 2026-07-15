"""Add GIN trigram indexes for partial ILIKE search performance

Adds GIN trigram indexes on all text columns searched via ILIKE in
CompanySearchRepository. Without these, LIKE/ILIKE with leading % causes
sequential scans (p95 2668ms for partial name_ar search at 100k rows).

Affected columns:
  - companies.name_ar     (worst offender: p95 2668ms → expected < 50ms)
  - companies.name_en
  - companies.cr_number
  - companies.city
  - companies.region
  - companies.activity_description

Revision ID: 0029
Revises: 0028
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0029"
down_revision: Union[str, None] = "0028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_name_ar_trgm "
        "ON companies USING GIN (name_ar gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_name_en_trgm "
        "ON companies USING GIN (name_en gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_cr_number_trgm "
        "ON companies USING GIN (cr_number gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_city_trgm "
        "ON companies USING GIN (city gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_region_trgm "
        "ON companies USING GIN (region gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_activity_desc_trgm "
        "ON companies USING GIN (activity_description gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_companies_name_ar_trgm")
    op.execute("DROP INDEX IF EXISTS idx_companies_name_en_trgm")
    op.execute("DROP INDEX IF EXISTS idx_companies_cr_number_trgm")
    op.execute("DROP INDEX IF EXISTS idx_companies_city_trgm")
    op.execute("DROP INDEX IF EXISTS idx_companies_region_trgm")
    op.execute("DROP INDEX IF EXISTS idx_companies_activity_desc_trgm")
