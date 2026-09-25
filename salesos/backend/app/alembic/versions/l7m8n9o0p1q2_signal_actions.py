"""Signal Actions: qualification, priority, NBA, and sales action tables.

Tables:
- agent_signal_qualifications: qualified signals with priority scores
- agent_account_priorities: account intent scores + recommended actions
- agent_next_best_actions: NBA recommendations
- agent_sales_actions: executed sales action audit trail

All tables carry tenant_id for RLS isolation.

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "l7m8n9o0p1q2"
down_revision = "k6l7m8n9o0p1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_signal_qualifications ────────────────────────────────
    op.create_table(
        "agent_signal_qualifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("signal_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("raw_confidence", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("priority_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("intent_contribution", sa.Float, nullable=False, server_default="0"),
        sa.Column("qualification_notes", sa.Text, nullable=False, server_default=""),
        sa.Column("qualified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
    )
    op.create_index("ix_asq_company", "agent_signal_qualifications", ["tenant_id", "company_name"])
    op.create_index("ix_asq_priority", "agent_signal_qualifications", ["tenant_id", "priority"])

    # ── agent_account_priorities ───────────────────────────────────
    op.create_table(
        "agent_account_priorities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("intent_level", sa.String(20), nullable=False),
        sa.Column("intent_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("signal_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("critical_signals", sa.Integer, nullable=False, server_default="0"),
        sa.Column("high_signals", sa.Integer, nullable=False, server_default="0"),
        sa.Column("recency_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("diversity_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("top_signal_types", JSONB, nullable=False, server_default="[]"),
        sa.Column("recommended_action", sa.String(50), nullable=False),
        sa.Column("action_urgency", sa.String(20), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
    )
    op.create_index("ix_aap_company", "agent_account_priorities", ["tenant_id", "company_name"], unique=True)
    op.create_index("ix_aap_intent", "agent_account_priorities", ["tenant_id", "intent_level"])

    # ── agent_next_best_actions ────────────────────────────────────
    op.create_table(
        "agent_next_best_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("urgency", sa.String(20), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("rationale", sa.Text, nullable=False, server_default=""),
        sa.Column("signal_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("channel", sa.String(50), nullable=False, server_default=""),
        sa.Column("suggested_message", sa.Text, nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
    )
    op.create_index("ix_anba_company", "agent_next_best_actions", ["tenant_id", "company_name"])
    op.create_index("ix_anba_urgency", "agent_next_best_actions", ["tenant_id", "urgency"])

    # ── agent_sales_actions ────────────────────────────────────────
    op.create_table(
        "agent_sales_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("nba_id", sa.String(36), nullable=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("outcome", sa.String(20), nullable=False, server_default=""),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
    )
    op.create_index("ix_asa_company", "agent_sales_actions", ["tenant_id", "company_name"])
    op.create_index("ix_asa_status", "agent_sales_actions", ["tenant_id", "status"])

    # ── RLS policies ───────────────────────────────────────────────
    for table in [
        "agent_signal_qualifications",
        "agent_account_priorities",
        "agent_next_best_actions",
        "agent_sales_actions",
    ]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation_{table} ON {table} "
            f"USING ((tenant_id)::text = current_setting('app.tenant_id'::text, true)) "
            f"WITH CHECK ((tenant_id)::text = current_setting('app.tenant_id'::text, true))"
        )
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in [
        "agent_sales_actions",
        "agent_next_best_actions",
        "agent_account_priorities",
        "agent_signal_qualifications",
    ]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.drop_table(table)
