"""hybrid search optimization: composite indexes and vector extension safety

Prepares the database for efficient hybrid (full-text + semantic) search:
  1. Ensures pgvector extension is created (idempotent)
  2. Adds composite index: (tenant_id, search_vector) for filtered full-text
  3. Adds composite index: (tenant_id, embedding_vector) — skip if HNSW exists
  4. Adds trigger to keep search_vector in sync on company field changes

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure pgvector extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Composite index for filtered full-text search.
    #    Most queries are tenant-scoped + full-text match. A composite index
    #    on (tenant_id, search_vector) lets PostgreSQL skip the row-level
    #    filter and jump straight to the GIN scan within the tenant partition.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_tenant_search_vector
        ON companies USING GIN(tenant_id, search_vector)
    """)

    # 3. Ensure HNSW index exists on embedding_vector for semantic search.
    #    This is a safety net — 0017 should have created it already.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_embedding_hnsw
        ON companies USING hnsw (embedding_vector vector_cosine_ops)
    """)

    # 4. Partial index: only companies with embeddings get indexed in HNSW.
    #    Reduces index size and speeds up insertion for companies without embeddings.
    #    (HNSW doesn't support partial indexes natively, so we skip this.)

    # 5. Trigger to auto-refresh search_vector when company fields change.
    #    This replaces the tsv trigger approach with the GENERATED ALWAYS column.
    #    The search_vector column (0023) is already GENERATED ALWAYS, so no
    #    trigger is needed for it. We just ensure the old tsv trigger stays
    #    in sync by adding a trigger that refreshes both.
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_companies_search_vectors() RETURNS trigger AS $$
        BEGIN
            -- search_vector is GENERATED ALWAYS, so it auto-updates.
            -- We only need to refresh tsv for backward compatibility.
            NEW.tsv := to_tsvector('simple',
                COALESCE(NEW.name_ar, '') || ' ' ||
                COALESCE(NEW.name_en, '') || ' ' ||
                COALESCE(NEW.cr_number, '') || ' ' ||
                COALESCE(NEW.city, '') || ' ' ||
                COALESCE(NEW.industry, '') || ' ' ||
                COALESCE(NEW.activity_description, '') || ' ' ||
                COALESCE(NEW.region, '') || ' ' ||
                COALESCE(NEW.legal_form, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_companies_search_vectors
            BEFORE INSERT OR UPDATE ON companies
            FOR EACH ROW EXECUTE FUNCTION refresh_companies_search_vectors()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_companies_search_vectors ON companies")
    op.execute("DROP FUNCTION IF EXISTS refresh_companies_search_vectors()")
    op.execute("DROP INDEX IF EXISTS idx_companies_tenant_search_vector")
    op.execute("DROP INDEX IF EXISTS idx_companies_embedding_hnsw")
