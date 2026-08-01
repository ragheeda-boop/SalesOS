"""DB-05 Slice 5c: CREATE TABLE for global admin trio (criterion 7.6).

Revision ID: e2b9d46f8a10
Revises: d1a8c35e7f09
Create Date: 2026-08-01

DEC-130c / DB-05 Slice 5c: additive CREATE only for
  - admin_plans
  - admin_feature_flags
  - admin_health_snapshots

Matches ORM in app/modules/admin/db_models.py (PlanModel, FeatureFlagModel,
HealthSnapshotModel). Global / platform tables — no tenant_id, no ENABLE RLS.
Does NOT touch get_db() / DEC-085 set_config.
Idempotent: skip create when table already exists (init_db drift).
Does NOT DROP. Does NOT run on Railway / production this land.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e2b9d46f8a10"
down_revision: Union[str, None] = "d1a8c35e7f09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "admin_plans"):
        op.create_table(
            "admin_plans",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("tier", sa.String(50), nullable=False),
            sa.Column("price_monthly", sa.Float(), nullable=False, server_default="0"),
            sa.Column("price_yearly", sa.Float(), nullable=False, server_default="0"),
            sa.Column("max_users", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("max_storage_mb", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("max_api_calls", sa.Integer(), nullable=False, server_default="1000"),
            sa.Column(
                "features",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists(conn, "admin_feature_flags"):
        op.create_table(
            "admin_feature_flags",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("key", sa.String(100), unique=True, nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_global", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column(
                "tenant_overrides",
                postgresql.JSONB(),
                nullable=True,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_ci_test", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    if not _table_exists(conn, "admin_health_snapshots"):
        op.create_table(
            "admin_health_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("overall_status", sa.String(50), nullable=False),
            sa.Column("components", postgresql.JSONB(), nullable=False),
        )
        op.create_index("ix_admin_health_ts", "admin_health_snapshots", ["timestamp"])


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "admin_health_snapshots"):
        op.drop_index("ix_admin_health_ts", table_name="admin_health_snapshots")
        op.drop_table("admin_health_snapshots")
    if _table_exists(conn, "admin_feature_flags"):
        op.drop_table("admin_feature_flags")
    if _table_exists(conn, "admin_plans"):
        op.drop_table("admin_plans")
