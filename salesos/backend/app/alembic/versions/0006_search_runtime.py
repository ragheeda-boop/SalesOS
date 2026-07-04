"""search runtime: add embedding column to companies table

Creates:
  - companies.embedding (vector(3072) for text-embedding-3-large)
  - companies.tsv column + GIN index for full-text search
  - Search index (IVFFlat) for fast approximate nearest neighbor

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Vector embedding column ─────────────────────────────────
    op.add_column(
        "companies",
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),
    )
    # Native pgvector column (if vector extension is available)
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS embedding_vector vector(3072)")

    # ── Full-text search column ─────────────────────────────────
    op.add_column(
        "companies",
        sa.Column("tsv", postgresql.TSVECTOR, nullable=True),
    )

    # Populate tsv from existing data
    op.execute("""
        UPDATE companies SET tsv = 
            to_tsvector('arabic', COALESCE(name_ar, '') || ' ' ||
                                 COALESCE(name_en, '') || ' ' ||
                                 COALESCE(cr_number, '') || ' ' ||
                                 COALESCE(activity_description, '') || ' ' ||
                                 COALESCE(city, '') || ' ' ||
                                 COALESCE(industry, ''))
    """)

    # GIN index on tsv for fast full-text search
    op.create_index("ix_companies_tsv", "companies", ["tsv"],
                    postgresql_using="gin")

    # Auto-refresh tsv on insert/update
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_companies_tsv() RETURNS trigger AS $$
        BEGIN
            NEW.tsv := to_tsvector('arabic', COALESCE(NEW.name_ar, '') || ' ' ||
                                      COALESCE(NEW.name_en, '') || ' ' ||
                                      COALESCE(NEW.cr_number, '') || ' ' ||
                                      COALESCE(NEW.activity_description, '') || ' ' ||
                                      COALESCE(NEW.city, '') || ' ' ||
                                      COALESCE(NEW.industry, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_companies_tsv
            BEFORE INSERT OR UPDATE ON companies
            FOR EACH ROW EXECUTE FUNCTION refresh_companies_tsv()
    """)

    # IVFFlat index for approximate nearest neighbor
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_companies_embedding_vector 
        ON companies 
        USING ivfflat (embedding_vector vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_companies_tsv ON companies")
    op.execute("DROP FUNCTION IF EXISTS refresh_companies_tsv()")
    op.drop_index("ix_companies_tsv", table_name="companies")
    op.drop_index("ix_companies_embedding_vector", table_name="companies")
    op.drop_column("companies", "embedding_vector")
    op.drop_column("companies", "tsv")
    op.drop_column("companies", "embedding")
