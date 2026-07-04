"""commercial domain: create tables for all 10 business domains

Creates:
  - commercial_opportunities — sales opportunities
  - commercial_stage_entries — pipeline stage transitions
  - commercial_pipeline_definitions — pipeline configuration
  - commercial_activity_sessions — grouped activity sessions
  - commercial_activities — individual activities within sessions
  - commercial_quotes — sales quotes
  - commercial_quote_lines — individual quote line items
  - commercial_proposals — sales proposals
  - commercial_contracts — signed contracts
  - commercial_forecast_snapshots — revenue forecasts
  - commercial_analytics_snapshots — analytics/KPI snapshots
  - commercial_decision_contexts — decision context factors
  - commercial_policies — business policy rules
  - commercial_recommendations — AI recommendations

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Opportunities ──────────────────────────────────────────
    op.create_table(
        "commercial_opportunities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("company_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("value", sa.Float, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="SAR"),
        sa.Column("stage", sa.String(100), nullable=False, server_default="prospecting"),
        sa.Column("probability", sa.Float, nullable=False, server_default="0.1"),
        sa.Column("expected_close_date", sa.Date, nullable=True),
        sa.Column("owner_id", sa.String(36), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("won_amount", sa.Float, nullable=True),
        sa.Column("loss_reason", sa.Text, nullable=False, server_default=""),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("tags", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("metadata", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Stage Entries (pipeline transitions) ──────────────────
    op.create_table(
        "commercial_stage_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False, index=True),
        sa.Column("pipeline_id", sa.String(36), nullable=False, index=True),
        sa.Column("from_stage", sa.String(100), nullable=False),
        sa.Column("to_stage", sa.String(100), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_hours", sa.Float, nullable=True),
    )
    op.create_foreign_key(
        "fk_stage_entries_opportunity",
        "commercial_stage_entries", "commercial_opportunities",
        ["opportunity_id"], ["id"],
    )

    # ── Pipeline Definitions ───────────────────────────────────
    op.create_table(
        "commercial_pipeline_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("stages", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Activity Sessions ──────────────────────────────────────
    op.create_table(
        "commercial_activity_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=False, server_default="opportunity"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Activities ─────────────────────────────────────────────
    op.create_table(
        "commercial_activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=False, index=True),
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("owner_name", sa.String(200), nullable=False, server_default=""),
        sa.Column("outcome_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("outcome_label", sa.String(200), nullable=False, server_default=""),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("external_id", sa.String(200), nullable=False, server_default=""),
    )
    op.create_foreign_key(
        "fk_activities_session",
        "commercial_activities", "commercial_activity_sessions",
        ["session_id"], ["id"],
    )

    # ── Quotes ─────────────────────────────────────────────────
    op.create_table(
        "commercial_quotes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("total_value", sa.Float, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="SAR"),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(36), nullable=False, server_default=""),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Quote Lines ────────────────────────────────────────────
    op.create_table(
        "commercial_quote_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("quote_id", sa.String(36), nullable=False, index=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Float, nullable=False, server_default="0"),
        sa.Column("total", sa.Float, nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        "fk_quote_lines_quote",
        "commercial_quote_lines", "commercial_quotes",
        ["quote_id"], ["id"],
    )

    # ── Proposals ──────────────────────────────────────────────
    op.create_table(
        "commercial_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False, index=True),
        sa.Column("quote_id", sa.String(36), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("delivery_method", sa.String(100), nullable=False, server_default=""),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=False, server_default=""),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Contracts ──────────────────────────────────────────────
    op.create_table(
        "commercial_contracts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False, index=True),
        sa.Column("quote_id", sa.String(36), nullable=False),
        sa.Column("quote_revision", sa.Integer, nullable=False, server_default="1"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("parties", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("obligations", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("effective_date", sa.Date, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("renewal", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("legal_terms", sa.Text, nullable=False, server_default=""),
        sa.Column("governing_law", sa.String(100), nullable=False, server_default=""),
        sa.Column("signed_by_provider", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by_customer", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Forecast Snapshots ─────────────────────────────────────
    op.create_table(
        "commercial_forecast_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("horizon_months", sa.Integer, nullable=False, server_default="3"),
        sa.Column("status", sa.String(20), nullable=False, server_default="calculated"),
        sa.Column("lines", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("assumptions", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )

    # ── Analytics Snapshots ────────────────────────────────────
    op.create_table(
        "commercial_analytics_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("kpis", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("insights", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Decision Contexts ──────────────────────────────────────
    op.create_table(
        "commercial_decision_contexts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("factors", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Policies ───────────────────────────────────────────────
    op.create_table(
        "commercial_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("rules", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Recommendations ────────────────────────────────────────
    op.create_table(
        "commercial_recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("recommendation_type", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("evidence", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("alternatives", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Indexes ────────────────────────────────────────────────
    # Additional composite indexes for common queries
    op.create_index("ix_opportunities_tenant_stage", "commercial_opportunities", ["tenant_id", "stage"])
    op.create_index("ix_opportunities_tenant_status", "commercial_opportunities", ["tenant_id", "status"])
    op.create_index("ix_activities_session_type", "commercial_activities", ["session_id", "activity_type"])
    op.create_index("ix_quotes_opportunity_status", "commercial_quotes", ["opportunity_id", "status"])
    op.create_index("ix_contracts_tenant_status", "commercial_contracts", ["tenant_id", "status"])
    op.create_index("ix_recommendations_target", "commercial_recommendations", ["target_id", "target_type"])
    op.create_index("ix_decision_contexts_target", "commercial_decision_contexts", ["target_id", "target_type"])


def downgrade() -> None:
    op.drop_table("commercial_recommendations")
    op.drop_table("commercial_policies")
    op.drop_table("commercial_decision_contexts")
    op.drop_table("commercial_analytics_snapshots")
    op.drop_table("commercial_forecast_snapshots")
    op.drop_table("commercial_contracts")
    op.drop_table("commercial_proposals")
    op.drop_table("commercial_quote_lines")
    op.drop_table("commercial_quotes")
    op.drop_table("commercial_activities")
    op.drop_table("commercial_activity_sessions")
    op.drop_table("commercial_pipeline_definitions")
    op.drop_table("commercial_stage_entries")
    op.drop_table("commercial_opportunities")
