"""rag: create rag_documents and rag_document_chunks tables

Creates:
  - rag_documents — document metadata for RAG retrieval
  - rag_document_chunks — chunked content with pgvector embeddings

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # rag: create rag_documents table
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rag_chunks_tenant", "rag_documents", ["tenant_id"])

    # rag: create rag_document_chunks table
    op.create_table(
        "rag_document_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["rag_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rag_chunks_document", "rag_document_chunks", ["document_id"])

    # Add pgvector embedding column and IVFFlat index
    op.execute("ALTER TABLE rag_document_chunks ADD COLUMN embedding vector(3072)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_rag_chunks_vector
        ON rag_document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_rag_chunks_vector")
    op.drop_index("idx_rag_chunks_document", table_name="rag_document_chunks")
    op.drop_index("idx_rag_chunks_tenant", table_name="rag_documents")
    op.drop_table("rag_document_chunks")
    op.drop_table("rag_documents")
