"""Observation snapshot + score versioning

Adds score versioning and append-only observation history to enable calibration analysis.

Revision ID: o0p1q2r3s4t5
"""
from alembic import op
import sqlalchemy as sa

revision = "o0p1q2r3s4t5"
down_revision = "n9o0p1q2r3s4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add score versioning columns to account_funnel
    op.add_column("account_funnel", sa.Column("intent_model_version", sa.String(20), nullable=False, server_default="v1"))
    op.add_column("account_funnel", sa.Column("score_observed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("account_funnel", sa.Column("signal_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("account_funnel", sa.Column("critical_signal_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("account_funnel", sa.Column("source_diversity", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("account_funnel", sa.Column("nba_type", sa.String(50), nullable=True))
    op.add_column("account_funnel", sa.Column("nba_urgency", sa.String(20), nullable=True))
    op.add_column("account_funnel", sa.Column("original_nba_type", sa.String(50), nullable=True))
    op.add_column("account_funnel", sa.Column("seller_selected_action", sa.String(50), nullable=True))
    op.add_column("account_funnel", sa.Column("time_to_first_action_hours", sa.Float(), nullable=True))
    op.add_column("account_funnel", sa.Column("observation_cohort_at", sa.DateTime(timezone=True), nullable=True))

    # Indexes for versioning queries
    op.create_index("ix_af_model_version", "account_funnel", ["intent_model_version"])
    op.create_index("ix_af_observed_at", "account_funnel", ["score_observed_at"])

    # 2. Append-only observation log for score changes
    op.create_table(
        "score_observations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),

        # Score snapshot (immutable at time of observation)
        sa.Column("intent_score", sa.Float(), nullable=False),
        sa.Column("intent_level", sa.String(20), nullable=False),
        sa.Column("cohort", sa.String(20), nullable=False),
        sa.Column("intent_model_version", sa.String(20), nullable=False, server_default="v1"),

        # Signal context at time of observation
        sa.Column("signal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_signal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("signal_types", sa.JSON(), nullable=True),
        sa.Column("source_diversity", sa.Integer(), nullable=False, server_default="0"),

        # CRM context at time of observation
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("company_size", sa.String(50), nullable=True),
        sa.Column("has_opportunity", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_activity_days", sa.Integer(), nullable=True),

        # NBA context at time of observation
        sa.Column("nba_type", sa.String(50), nullable=True),
        sa.Column("nba_urgency", sa.String(20), nullable=True),
        sa.Column("nba_confidence", sa.Float(), nullable=True),
        sa.Column("nba_accepted", sa.Boolean(), nullable=True),

        # Outcome context (filled in later, nullable)
        sa.Column("first_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_action_type", sa.String(50), nullable=True),
        sa.Column("connection_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opportunity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proposal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("won_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lost_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),

        # Metadata
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # RLS on score_observations
    op.execute("ALTER TABLE score_observations ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_score_observations ON score_observations
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)

    # Indexes for score_observations
    op.create_index("ix_so_tenant_company", "score_observations", ["tenant_id", "company_name"])
    op.create_index("ix_so_tenant_cohort", "score_observations", ["tenant_id", "cohort"])
    op.create_index("ix_so_tenant_version", "score_observations", ["tenant_id", "intent_model_version"])
    op.create_index("ix_so_observed_at", "score_observations", ["observed_at"])
    op.create_index("ix_so_tenant_seller", "score_observations", ["tenant_id", "seller_id"])

    # Unique constraint: one observation per company per version per timestamp-hour
    # (allows multiple observations if rescoring happens on different days)
    op.create_index("ix_so_company_observed", "score_observations", ["tenant_id", "company_name", "observed_at"])


def downgrade() -> None:
    op.drop_table("score_observations")
    op.drop_index("ix_af_observed_at", "account_funnel")
    op.drop_index("ix_af_model_version", "account_funnel")
    op.drop_column("account_funnel", "observation_cohort_at")
    op.drop_column("account_funnel", "time_to_first_action_hours")
    op.drop_column("account_funnel", "seller_selected_action")
    op.drop_column("account_funnel", "original_nba_type")
    op.drop_column("account_funnel", "nba_urgency")
    op.drop_column("account_funnel", "nba_type")
    op.drop_column("account_funnel", "source_diversity")
    op.drop_column("account_funnel", "critical_signal_count")
    op.drop_column("account_funnel", "signal_count")
    op.drop_column("account_funnel", "score_observed_at")
    op.drop_column("account_funnel", "intent_model_version")
