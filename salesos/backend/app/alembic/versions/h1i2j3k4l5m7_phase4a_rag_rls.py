"""Phase 4A: Row-Level Security for RAG tables (canonical DEC-085 pattern).

rag_documents carries tenant_id directly; rag_document_chunks has NO tenant_id
by design — its tenancy derives from the parent document via FK. The chunks
policy therefore authorizes through an EXISTS probe on rag_documents so chunk
access can never bypass document tenancy.

Policy shape mirrors pg_policies['tenant_isolation_companies'] exactly:
  (tenant_id)::text = current_setting('app.tenant_id'::text, true)
which is fail-closed (NULL GUC -> no rows, blocked writes).

Revision ID: h1i2j3k4l5m7
Revises: g1h2i3j4k5l6
Create Date: 2026-08-23
"""
from alembic import op

revision = "h1i2j3k4l5m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── rag_documents ────────────────────────────────────────────────
    op.execute("ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_rag_documents ON rag_documents "
        "USING ((tenant_id)::text = current_setting('app.tenant_id'::text, true)) "
        "WITH CHECK ((tenant_id)::text = current_setting('app.tenant_id'::text, true))"
    )
    op.execute("ALTER TABLE rag_documents FORCE ROW LEVEL SECURITY")

    # ── rag_document_chunks (tenancy via parent document) ────────────
    op.execute("ALTER TABLE rag_document_chunks ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_rag_document_chunks ON rag_document_chunks "
        "USING (EXISTS ("
        "  SELECT 1 FROM rag_documents d "
        "  WHERE d.id = rag_document_chunks.document_id "
        "  AND (d.tenant_id)::text = current_setting('app.tenant_id'::text, true)"
        ")) "
        "WITH CHECK (EXISTS ("
        "  SELECT 1 FROM rag_documents d "
        "  WHERE d.id = rag_document_chunks.document_id "
        "  AND (d.tenant_id)::text = current_setting('app.tenant_id'::text, true)"
        "))"
    )
    op.execute("ALTER TABLE rag_document_chunks FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_rag_document_chunks "
        "ON rag_document_chunks"
    )
    op.execute("ALTER TABLE rag_document_chunks NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rag_document_chunks DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_rag_documents ON rag_documents")
    op.execute("ALTER TABLE rag_documents NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rag_documents DISABLE ROW LEVEL SECURITY")
