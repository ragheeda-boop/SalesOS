"""Create marketplace plugin tables

Revision ID: 0036
Revises: 0035
Create Date: 2026-07-16

Idempotent: skips tables/indexes that already exist.
Note: do not set index=True on state/enabled — that collides with the
composite ix_marketplace_plugins_state name.
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def _index_exists(conn, table: str, index_name: str) -> bool:
    inspector = sa.inspect(conn)
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "marketplace_plugins"):
        op.create_table(
            "marketplace_plugins",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("plugin_id", sa.String(64), unique=True, nullable=False, index=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("version", sa.String(16), nullable=False),
            sa.Column("description", sa.Text, default=""),
            sa.Column("author", sa.String(128), default=""),
            sa.Column("license", sa.String(32), default="MIT"),
            sa.Column("icon", sa.String(512), nullable=True),
            sa.Column("tags", JSONB, nullable=True, default=list),
            sa.Column("permissions", JSONB, nullable=True, default=list),
            sa.Column("hooks", JSONB, nullable=True, default=list),
            sa.Column("widgets", JSONB, nullable=True, default=list),
            sa.Column("dependencies", JSONB, nullable=True, default=list),
            sa.Column("config_schema", JSONB, nullable=True),
            sa.Column("resource_limits", JSONB, nullable=True),
            sa.Column("config", JSONB, nullable=True, default=dict),
            # No index=True here — composite index below owns the name
            sa.Column("state", sa.String(20), default="active"),
            sa.Column("enabled", sa.Boolean, default=True),
            sa.Column("call_count", sa.Integer, default=0),
            sa.Column("error_count", sa.Integer, default=0),
            sa.Column("last_error", sa.Text, nullable=True),
            sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    if _table_exists(conn, "marketplace_plugins") and not _index_exists(
        conn, "marketplace_plugins", "ix_marketplace_plugins_state"
    ):
        op.create_index(
            "ix_marketplace_plugins_state",
            "marketplace_plugins",
            ["state", "enabled"],
        )

    if not _table_exists(conn, "marketplace_lifecycle_events"):
        op.create_table(
            "marketplace_lifecycle_events",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("plugin_id", sa.String(64), nullable=False, index=True),
            sa.Column("from_state", sa.String(20), nullable=True),
            sa.Column("to_state", sa.String(20), nullable=False),
            sa.Column("metadata", JSONB, nullable=True, default=dict),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        )
    if _table_exists(conn, "marketplace_lifecycle_events") and not _index_exists(
        conn, "marketplace_lifecycle_events", "ix_marketplace_lifecycle_plugin_ts"
    ):
        op.create_index(
            "ix_marketplace_lifecycle_plugin_ts",
            "marketplace_lifecycle_events",
            ["plugin_id", "timestamp"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "marketplace_lifecycle_events"):
        op.drop_table("marketplace_lifecycle_events")
    if _table_exists(conn, "marketplace_plugins"):
        op.drop_table("marketplace_plugins")
