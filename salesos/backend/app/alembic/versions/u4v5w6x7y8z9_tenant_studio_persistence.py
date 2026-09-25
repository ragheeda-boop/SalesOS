"""Persist tenant-owned Prompt Library and AI Policy Studio documents.

Revision ID: u4v5w6x7y8z9
Revises: t3u4v5w6x7
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "u4v5w6x7y8z9"
down_revision: str | None = "t3u4v5w6x7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_studio_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(32), nullable=False),
        sa.Column("document_key", sa.String(64), nullable=False),
        sa.Column("logical_key", sa.String(128)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "tenant_id", "document_type", "document_key", name="uq_tenant_studio_document_key"
        ),
        sa.CheckConstraint(
            "document_type IN ('prompt_library', 'ai_policies')",
            name="ck_tenant_studio_document_type",
        ),
    )
    op.create_index(
        "ix_tenant_studio_documents_tenant_type_updated",
        "tenant_studio_documents",
        ["tenant_id", "document_type", "updated_at"],
    )
    op.create_index(
        "uq_tenant_studio_prompt_logical_key",
        "tenant_studio_documents",
        ["tenant_id", "logical_key"],
        unique=True,
        postgresql_where=sa.text("document_type = 'prompt_library' AND logical_key IS NOT NULL"),
    )
    op.execute("ALTER TABLE tenant_studio_documents ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_tenant_studio_documents "
        "ON tenant_studio_documents FOR ALL "
        "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute("ALTER TABLE tenant_studio_documents FORCE ROW LEVEL SECURITY")
    op.execute(sa.text("REVOKE ALL ON tenant_studio_documents FROM PUBLIC"))
    op.execute(
        sa.text(
            "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') "
            "THEN EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_studio_documents TO salesos_app'; "
            "END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_tenant_studio_documents "
        "ON tenant_studio_documents"
    )
    op.execute("ALTER TABLE tenant_studio_documents NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant_studio_documents DISABLE ROW LEVEL SECURITY")
    op.drop_index(
        "ix_tenant_studio_documents_tenant_type_updated", table_name="tenant_studio_documents"
    )
    op.drop_index("uq_tenant_studio_prompt_logical_key", table_name="tenant_studio_documents")
    op.drop_table("tenant_studio_documents")
