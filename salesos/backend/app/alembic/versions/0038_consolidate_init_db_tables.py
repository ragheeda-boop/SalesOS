"""Consolidate tables previously created by init_db() raw SQL and add decision_center tables

Creates:
  - sso_connections — ORM model, was created by init_db() raw SQL
  - audit_logs — ORM model, was created by init_db() raw SQL (0037 adds outcome column)
  - api_keys — ORM model, was created by init_db() raw SQL
  - decision_center_decisions — new for PostgresDecisionCenterRepository
  - decision_center_audits — new for PostgresDecisionCenterRepository
  - decision_center_feedback — new for PostgresDecisionCenterRepository
  - decision_center_templates — new for PostgresDecisionCenterRepository

Revision ID: 0038
Revises: 0037
Create Date: 2026-07-17

Idempotent: skips tables already present from init_db (PROD-W1-001 local drift fix).
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0038"
down_revision: str | None = "0037"
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

    # ── sso_connections (was created by init_db raw SQL) ──────────
    if not _table_exists(conn, "sso_connections"):
        op.create_table(
            "sso_connections",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("provider_user_id", sa.String(255), nullable=False),
            sa.Column("provider_email", sa.String(255), nullable=True),
            sa.Column("access_token", sa.Text, nullable=True),
            sa.Column("refresh_token", sa.Text, nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_sso_user_provider", "sso_connections", ["user_id", "provider"])
    elif not _index_exists(conn, "sso_connections", "ix_sso_user_provider"):
        op.create_index("ix_sso_user_provider", "sso_connections", ["user_id", "provider"])

    # ── audit_logs (was created by init_db raw SQL; 0037 adds outcome) ──
    if not _table_exists(conn, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
            sa.Column("user_id", sa.String(64), nullable=True, index=True),
            sa.Column("action", sa.String(100), nullable=False, index=True),
            sa.Column("resource_type", sa.String(100), nullable=False, index=True),
            sa.Column("resource_id", sa.String(255), nullable=True),
            sa.Column("details", JSONB, nullable=True, server_default="{}"),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.Text, nullable=True),
            sa.Column("request_id", sa.String(100), nullable=True),
            sa.Column("outcome", sa.String(20), nullable=False, server_default="success"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        )
        op.create_index(
            "ix_audit_logs_tenant_action",
            "audit_logs",
            ["tenant_id", "action", sa.text("created_at DESC")],
        )
        op.create_index(
            "ix_audit_logs_tenant_resource",
            "audit_logs",
            ["tenant_id", "resource_type", sa.text("created_at DESC")],
        )

    # ── api_keys (was created by init_db raw SQL) ─────────────────
    if not _table_exists(conn, "api_keys"):
        op.create_table(
            "api_keys",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("key_prefix", sa.String(10), nullable=False),
            sa.Column("key_hash", sa.String(255), nullable=False),
            sa.Column("permissions", JSONB, nullable=True, server_default="{}"),
            sa.Column("scopes", sa.Text, nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_revoked", sa.Boolean, nullable=False, server_default=sa.text("false")),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_api_keys_prefix", "api_keys", ["key_prefix"])
        op.create_index("ix_api_keys_user", "api_keys", ["user_id"])

    # ── decision_center_decisions ─────────────────────────────────
    if not _table_exists(conn, "decision_center_decisions"):
        op.create_table(
            "decision_center_decisions",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("domain", sa.String(50), nullable=False, index=True),
            sa.Column("decision_type", sa.String(50), nullable=False, index=True),
            sa.Column("entity_id", sa.String(255), nullable=False, index=True),
            sa.Column("entity_type", sa.String(50), nullable=False),
            sa.Column("decision", sa.Text, nullable=False),
            sa.Column("confidence", sa.Float, nullable=False),
            sa.Column("reasoning", sa.Text, nullable=True),
            sa.Column("provider", sa.String(100), nullable=False),
            sa.Column("alternatives", JSONB, nullable=True),
            sa.Column("decision_metadata", JSONB, nullable=True),
            sa.Column("is_ensemble", sa.Boolean, nullable=False, server_default=sa.text("false")),
            sa.Column("ensemble_votes", JSONB, nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_dcd_entity", "decision_center_decisions", ["entity_type", "entity_id"])
        op.create_index("ix_dcd_status", "decision_center_decisions", ["status"])

    # ── decision_center_audits ────────────────────────────────────
    if not _table_exists(conn, "decision_center_audits"):
        op.create_table(
            "decision_center_audits",
            sa.Column("decision_id", sa.String(64), primary_key=True),
            sa.Column("input_context", JSONB, nullable=True),
            sa.Column("reasoning_steps", JSONB, nullable=True),
            sa.Column("confidence_breakdown", JSONB, nullable=True),
            sa.Column("provider_used", sa.String(100), nullable=False),
            sa.Column("alternatives_considered", JSONB, nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ensemble_metadata", JSONB, nullable=True),
        )

    # ── decision_center_feedback ──────────────────────────────────
    if not _table_exists(conn, "decision_center_feedback"):
        op.create_table(
            "decision_center_feedback",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("decision_id", sa.String(64), nullable=False, index=True),
            sa.Column("rating", sa.String(10), nullable=False),
            sa.Column("comment", sa.Text, nullable=True),
            sa.Column("actor_id", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_dcf_decision", "decision_center_feedback", ["decision_id"])

    # ── decision_center_templates ─────────────────────────────────
    if not _table_exists(conn, "decision_center_templates"):
        op.create_table(
            "decision_center_templates",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("template_type", sa.String(50), nullable=False, index=True),
            sa.Column("config", JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    conn = op.get_bind()
    for table in (
        "decision_center_templates",
        "decision_center_feedback",
        "decision_center_audits",
        "decision_center_decisions",
    ):
        if _table_exists(conn, table):
            op.drop_table(table)
    # Do not drop api_keys / audit_logs / sso_connections on downgrade when
    # they may have been created by init_db outside this revision's ownership.
