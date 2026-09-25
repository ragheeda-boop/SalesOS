"""Persist opt-in conversation memory with tenant RLS.

Revision ID: w6x7y8z9a0b1
Revises: v5w6x7y8z9a0
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "w6x7y8z9a0b1"
down_revision: str | None = "v5w6x7y8z9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enable_tenant_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation_{table} ON {table} FOR ALL "
        "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(sa.text(f"REVOKE ALL ON {table} FROM PUBLIC"))
    op.execute(
        sa.text(
            "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') "
            f"THEN EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO salesos_app'; "
            "END IF; END $grant$;"
        )
    )


def upgrade() -> None:
    op.create_table(
        "tenant_ai_memory_settings",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_turns", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("retention_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("max_turns BETWEEN 1 AND 200", name="ck_ai_memory_max_turns"),
        sa.CheckConstraint(
            "retention_hours BETWEEN 1 AND 168", name="ck_ai_memory_retention_hours"
        ),
    )
    op.create_table(
        "tenant_ai_memory_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("conversation_id", sa.String(128), nullable=False),
        # JSON contains Fernet ciphertext only; plaintext is never stored in Postgres.
        sa.Column("encrypted_turns", postgresql.JSONB(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "tenant_id", "conversation_id", name="uq_tenant_ai_memory_conversation"
        ),
        sa.CheckConstraint("schema_version >= 1", name="ck_ai_memory_schema_version"),
    )
    op.create_index(
        "ix_tenant_ai_memory_expiry",
        "tenant_ai_memory_conversations",
        ["tenant_id", "expires_at"],
    )
    _enable_tenant_rls("tenant_ai_memory_settings")
    _enable_tenant_rls("tenant_ai_memory_conversations")


def downgrade() -> None:
    for table in ("tenant_ai_memory_conversations", "tenant_ai_memory_settings"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_tenant_ai_memory_expiry", table_name="tenant_ai_memory_conversations")
    op.drop_table("tenant_ai_memory_conversations")
    op.drop_table("tenant_ai_memory_settings")
