"""Create employee_oauth_tokens table for Google/Microsoft OAuth integration.

Revision ID: 0045
Revises: 0044
"""

from typing import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0045"
down_revision: str | None = "0044"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(conn, table: str) -> bool:
    return table in sa.inspect(conn).get_table_names()


def _index_exists(conn, table: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in sa.inspect(conn).get_indexes(table))


def upgrade() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, "employee_oauth_tokens"):
        op.create_table(
            "employee_oauth_tokens",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("provider", sa.String(20), nullable=False),
            sa.Column("scope", sa.String(500), nullable=True),
            sa.Column("access_token_encrypted", sa.Text, nullable=True),
            sa.Column("refresh_token_encrypted", sa.Text, nullable=True),
            sa.Column("id_token_encrypted", sa.Text, nullable=True),
            sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("calendar_sync_token", sa.String(500), nullable=True),
            sa.Column("calendar_delta_link", sa.String(1000), nullable=True),
            sa.Column("email_history_id", sa.String(500), nullable=True),
            sa.Column("email_delta_link", sa.String(1000), nullable=True),
            sa.Column("last_calendar_sync_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_email_sync_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("webhook_channel_id", sa.String(255), nullable=True),
            sa.Column("webhook_resource_id", sa.String(255), nullable=True),
            sa.Column("webhook_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean, server_default="true"),
            sa.Column("is_connected", sa.Boolean, server_default="false"),
            sa.Column("connection_error", sa.Text, nullable=True),
            sa.Column("consecutive_failures", sa.Integer, server_default="0"),
            sa.Column("max_failures", sa.Integer, server_default="10"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    for name, cols in (
        ("ix_oauth_tokens_employee_provider", ["employee_id", "provider"]),
        ("ix_oauth_tokens_tenant", ["tenant_id"]),
        ("ix_oauth_tokens_expires", ["access_token_expires_at"]),
        ("ix_oauth_tokens_webhook_channel", ["webhook_channel_id"]),
    ):
        if _table_exists(conn, "employee_oauth_tokens") and not _index_exists(conn, "employee_oauth_tokens", name):
            op.create_index(name, "employee_oauth_tokens", cols, unique=(name == "ix_oauth_tokens_employee_provider"))


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "employee_oauth_tokens"):
        op.drop_table("employee_oauth_tokens")
