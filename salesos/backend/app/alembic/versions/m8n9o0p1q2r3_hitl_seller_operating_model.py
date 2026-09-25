"""Human-in-the-Loop: NBA feedback, action outcomes, and sales follow-ups.

Tables:
- nba_feedback: seller decisions on NBA (accept/reject/modify) with provenance
- action_outcomes: call/email/meeting results with outcome classification
- sales_followups: generated next actions linked to parent outcome

All tables carry tenant_id for RLS isolation.
Parent linkage preserves full decision chain: recommendation -> feedback -> outcome -> follow-up.

Revision ID: m8n9o0p1q2r3
Revises: l7m8n9o0p1q2
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "m8n9o0p1q2r3"
down_revision = "l7m8n9o0p1q2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── nba_feedback ────────────────────────────────────────────────
    op.create_table(
        "nba_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("action_id", UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),  # accepted, rejected, modified
        sa.Column("reason_code", sa.String(50), nullable=True),  # wrong_person, bad_timing, not_relevant, other
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("original_action_type", sa.String(50), nullable=False),
        sa.Column("modified_action_type", sa.String(50), nullable=True),
        sa.Column("modified_target_contact_id", sa.String(255), nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_nbf_company", "nba_feedback", ["tenant_id", "company_name"])
    op.create_index("ix_nbf_seller", "nba_feedback", ["tenant_id", "seller_id"])
    op.create_index("ix_nbf_decision", "nba_feedback", ["tenant_id", "decision"])
    op.create_index("ix_nbf_action", "nba_feedback", ["action_id"])

    # ── action_outcomes ─────────────────────────────────────────────
    op.create_table(
        "action_outcomes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("action_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("outcome_type", sa.String(50), nullable=False),
        # connected, no_answer, left_voicemail, email_sent, meeting_set,
        # positive, negative, neutral, proposal_sent
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("contact_reached", sa.String(255), nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("followup_required", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ao_company", "action_outcomes", ["tenant_id", "company_name"])
    op.create_index("ix_ao_seller", "action_outcomes", ["tenant_id", "seller_id"])
    op.create_index("ix_ao_outcome", "action_outcomes", ["tenant_id", "outcome_type"])
    op.create_index("ix_ao_action", "action_outcomes", ["action_id"])
    op.create_index("ix_ao_occurred", "action_outcomes", ["tenant_id", "occurred_at"])

    # ── sales_followups ─────────────────────────────────────────────
    op.create_table(
        "sales_followups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("parent_action_id", UUID(as_uuid=True), nullable=False),
        sa.Column("parent_outcome_id", UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("generated_action_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        # pending, completed, skipped, expired
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sf_company", "sales_followups", ["tenant_id", "company_name"])
    op.create_index("ix_sf_seller", "sales_followups", ["tenant_id", "seller_id"])
    op.create_index("ix_sf_status", "sales_followups", ["tenant_id", "status"])
    op.create_index("ix_sf_due", "sales_followups", ["tenant_id", "due_at"])
    op.create_index("ix_sf_parent_action", "sales_followups", ["parent_action_id"])

    # ── RLS policies ───────────────────────────────────────────────
    for table in ["nba_feedback", "action_outcomes", "sales_followups"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation_{table} ON {table} "
            f"USING ((tenant_id)::text = current_setting('app.tenant_id'::text, true)) "
            f"WITH CHECK ((tenant_id)::text = current_setting('app.tenant_id'::text, true))"
        )
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in ["sales_followups", "action_outcomes", "nba_feedback"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.drop_table(table)
