"""account_funnel + effectiveness_metrics

Revision ID: n9o0p1q2r3s4
"""
from alembic import op
import sqlalchemy as sa

revision = "n9o0p1q2r3s4"
down_revision = "m8n9o0p1q2r3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "account_funnel",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False, index=True),

        # Cohort assignment
        sa.Column("intent_score", sa.Integer(), nullable=False, default=0),
        sa.Column("intent_level", sa.String(20), nullable=False, default="LOW"),
        sa.Column("cohort", sa.String(20), nullable=False, default="baseline"),

        # Funnel events (timestamps, null = not reached)
        sa.Column("first_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_action_type", sa.String(50), nullable=True),
        sa.Column("first_action_id", sa.String(36), nullable=True),
        sa.Column("connection_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opportunity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proposal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("won_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lost_at", sa.DateTime(timezone=True), nullable=True),

        # Revenue
        sa.Column("deal_value", sa.Float(), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),

        # NBA feedback
        sa.Column("nba_accepted", sa.Integer(), nullable=False, default=0),
        sa.Column("nba_rejected", sa.Integer(), nullable=False, default=0),
        sa.Column("nba_modified", sa.Integer(), nullable=False, default=0),
        sa.Column("total_actions", sa.Integer(), nullable=False, default=0),
        sa.Column("total_outcomes", sa.Integer(), nullable=False, default=0),
        sa.Column("connected_outcomes", sa.Integer(), nullable=False, default=0),
        sa.Column("meeting_outcomes", sa.Integer(), nullable=False, default=0),

        # Signal metadata
        sa.Column("signal_types", sa.JSON(), nullable=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("company_size", sa.String(50), nullable=True),

        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        # Composite unique constraint
        sa.UniqueConstraint("tenant_id", "company_name", name="uq_account_funnel_tenant_company"),
    )

    # Indexes for common queries
    op.create_index("ix_account_funnel_tenant_cohort", "account_funnel", ["tenant_id", "cohort"])
    op.create_index("ix_account_funnel_tenant_seller", "account_funnel", ["tenant_id", "seller_id"])
    op.create_index("ix_account_funnel_tenant_level", "account_funnel", ["tenant_id", "intent_level"])
    op.create_index("ix_account_funnel_tenant_sector", "account_funnel", ["tenant_id", "sector"])
    op.create_index("ix_account_funnel_won", "account_funnel", ["tenant_id", "won_at"])

    # RLS
    op.execute("ALTER TABLE account_funnel ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_account_funnel ON account_funnel
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    op.drop_policy("tenant_isolation_account_funnel", "account_funnel")
    op.execute("ALTER TABLE account_funnel DISABLE ROW LEVEL SECURITY")
    op.drop_table("account_funnel")
