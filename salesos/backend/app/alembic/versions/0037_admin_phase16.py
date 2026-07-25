"""Phase 16: Admin — roles, permissions, role_permissions, tenant_configs, feature_flags enhancements, audit_logs outcome

Revision ID: 0037
Revises: 0036
Create Date: 2026-07-16

Idempotent: safe when admin tables/columns already exist (init_db drift).
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def _col_exists(conn, table: str, column: str) -> bool:
    inspector = sa.inspect(conn)
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()

    # ── admin_roles ────────────────────────────────────────────
    if not _table_exists(conn, "admin_roles"):
        op.create_table(
            "admin_roles",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text, default=""),
            sa.Column("is_system", sa.Boolean, default=False, nullable=False),
            sa.Column("tenant_id", sa.String(64), nullable=True, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # ── admin_permissions ──────────────────────────────────────
    if not _table_exists(conn, "admin_permissions"):
        op.create_table(
            "admin_permissions",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("key", sa.String(100), unique=True, nullable=False, index=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text, default=""),
            sa.Column("group", sa.String(50), default="general"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # ── admin_role_permissions ─────────────────────────────────
    if not _table_exists(conn, "admin_role_permissions"):
        op.create_table(
            "admin_role_permissions",
            sa.Column("role_id", sa.String(100), sa.ForeignKey("admin_roles.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("permission_id", sa.String(100), sa.ForeignKey("admin_permissions.id", ondelete="CASCADE"), primary_key=True),
        )

    # ── tenant_configs (YAML config editor) ────────────────────
    if not _table_exists(conn, "tenant_configs"):
        op.create_table(
            "tenant_configs",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
            sa.Column("key", sa.String(255), nullable=False),
            sa.Column("yaml_content", sa.Text, nullable=False),
            sa.Column("version", sa.Integer, nullable=False, default=1),
            sa.Column("created_by", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_tenant_configs_tenant_key", "tenant_configs", ["tenant_id", "key"])

    # ── feature_flags: add rollout_percentage, is_ci_test ──────
    if _table_exists(conn, "admin_feature_flags"):
        if not _col_exists(conn, "admin_feature_flags", "rollout_percentage"):
            op.add_column(
                "admin_feature_flags",
                sa.Column("rollout_percentage", sa.Integer, nullable=False, server_default="100"),
            )
        if not _col_exists(conn, "admin_feature_flags", "is_ci_test"):
            op.add_column(
                "admin_feature_flags",
                sa.Column("is_ci_test", sa.Boolean, nullable=False, server_default=sa.text("false")),
            )

    # ── audit_logs: add outcome ────────────────────────────────
    if _table_exists(conn, "audit_logs") and not _col_exists(conn, "audit_logs", "outcome"):
        op.add_column(
            "audit_logs",
            sa.Column("outcome", sa.String(20), nullable=False, server_default="success", index=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "audit_logs") and _col_exists(conn, "audit_logs", "outcome"):
        op.drop_column("audit_logs", "outcome")
    if _table_exists(conn, "admin_feature_flags"):
        if _col_exists(conn, "admin_feature_flags", "is_ci_test"):
            op.drop_column("admin_feature_flags", "is_ci_test")
        if _col_exists(conn, "admin_feature_flags", "rollout_percentage"):
            op.drop_column("admin_feature_flags", "rollout_percentage")
    if _table_exists(conn, "tenant_configs"):
        try:
            op.drop_index("ix_tenant_configs_tenant_key", "tenant_configs")
        except Exception:
            pass
        op.drop_table("tenant_configs")
    if _table_exists(conn, "admin_role_permissions"):
        op.drop_table("admin_role_permissions")
    if _table_exists(conn, "admin_permissions"):
        op.drop_table("admin_permissions")
    if _table_exists(conn, "admin_roles"):
        op.drop_table("admin_roles")
