"""decision intelligence engine: add decisions, feedback_loop, and policies tables

Creates:
  - public.decisions                (DecisionObject persistence)
  - public.decision_feedback_loop   (Feedback loop entries)
  - public.company_policies         (Dynamic business policies)

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Decisions (DecisionObject persistence) ─────────────────────
    op.create_table(
        "decisions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("decision_id", sa.String(64), nullable=False, unique=True),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("decision_type", sa.String(50), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("expected_revenue", sa.Float, nullable=True),
        sa.Column("expected_probability", sa.Float, nullable=True),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("evidence", postgresql.JSONB, nullable=True),
        sa.Column("supporting_features", postgresql.JSONB, nullable=True),
        sa.Column("context_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("required_actions", postgresql.JSONB, nullable=True),
        sa.Column("blocked_by", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="suggested"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_decisions_company", "decisions", ["tenant_id", "company_id"])
    op.create_index("ix_decisions_status", "decisions", ["tenant_id", "status"])
    op.create_index("ix_decisions_created", "decisions", [sa.text("created_at DESC")])

    # ── Decision Feedback Loop ────────────────────────────────────
    op.create_table(
        "decision_feedback_loop",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("decision_id", sa.String(64), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("user_accepted", sa.Boolean, nullable=False),
        sa.Column("executed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("outcome", sa.String(20), nullable=True),
        sa.Column("outcome_value", sa.Float, nullable=True),
        sa.Column("learning", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_feedback_decision", "decision_feedback_loop", ["decision_id"])
    op.create_index("ix_feedback_company", "decision_feedback_loop", ["tenant_id", "company_id"])

    # ── Business Policies (configurable per-company) ──────────────
    op.create_table(
        "company_policies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("policy_name", sa.String(100), nullable=False),
        sa.Column("policy_type", sa.String(50), nullable=False, server_default="custom"),
        sa.Column("action", sa.String(20), nullable=False, server_default="allow"),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("severity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_policies_company", "company_policies",
                    ["tenant_id", "company_id", "policy_name"], unique=True)

    # ── Add do_not_contact flag to companies ──────────────────────
    op.add_column(
        "companies",
        sa.Column("do_not_contact", sa.Boolean, nullable=False, server_default="false"),
    )

    # ── Seed default DNC policies for existing companies ──────────
    op.execute(
        "INSERT INTO company_policies (tenant_id, company_id, policy_name, policy_type, action, reason, severity) "
        "SELECT t.id::text, c.id::text, 'do_not_contact', 'builtin', 'block', 'Company has opted out of all contact', 5 "
        "FROM tenants t, companies c WHERE c.tenant_id = t.id AND c.do_not_contact = true "
        "ON CONFLICT (tenant_id, company_id, policy_name) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("company_policies")
    op.drop_table("decision_feedback_loop")
    op.drop_table("decisions")
    op.drop_column("companies", "do_not_contact")
