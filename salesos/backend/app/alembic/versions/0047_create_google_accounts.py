"""Create google_accounts table for Google Workspace integration.

Revision ID: 0047
Revises: 0045
Create Date: 2026-07-28

Note: 0046 was never committed; this revision correctly chains from 0045.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0047"
down_revision: Union[str, None] = "0045"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "google_accounts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False, server_default="google"),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("google_user_id", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("history_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_google_accounts_tenant_id", "google_accounts", ["tenant_id"])
    op.create_index("ix_google_accounts_user_id", "google_accounts", ["user_id"])
    op.create_index("ix_google_accounts_email", "google_accounts", ["email"])
    op.create_index(
        "ix_google_accounts_tenant_user",
        "google_accounts",
        ["tenant_id", "user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_google_accounts_tenant_user", table_name="google_accounts")
    op.drop_index("ix_google_accounts_email", table_name="google_accounts")
    op.drop_index("ix_google_accounts_user_id", table_name="google_accounts")
    op.drop_index("ix_google_accounts_tenant_id", table_name="google_accounts")
    op.drop_table("google_accounts")
