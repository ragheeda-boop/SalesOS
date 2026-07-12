"""Enable pg_trgm extension and trigram index on companies.name_ar

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_name_trgm "
        "ON companies USING GIN (name_ar gin_trgm_ops)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_companies_name_trgm")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
