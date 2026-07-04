"""feature store: add company_features and supporting data tables

Creates:
  - public.company_features           (cached computed scores per feature)
  - public.company_funding_events     (funding rounds data)
  - public.company_job_postings       (hiring/job posting data)
  - public.company_intent_rfps        (tender / RFP signals)
  - public.company_intent_visits      (web visit activity)
  - public.company_intent_content     (content consumption signals)
  - public.company_intent_contacts    (decision-maker interaction signals)
  - public.company_products           (product/service catalog)
  - public.company_deals              (deal / opportunity data)
  - public.company_payments           (payment history data)
  - public.companies.parent_company_id (for subsidiary expansion scoring)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add parent_company_id to companies ───────────────────────
    op.add_column(
        "companies",
        sa.Column("parent_company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id"), nullable=True, index=True),
    )
    op.add_column(
        "companies",
        sa.Column("annual_revenue", sa.Float, nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("revenue_prev_year", sa.Float, nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("revenue_2yr_ago", sa.Float, nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("employee_count_prev_year", sa.Integer, nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("linkedin_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("industry", sa.String(200), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("country", sa.String(100), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("branch_count", sa.Integer, nullable=True, server_default="0"),
    )

    # ── Company Features ─────────────────────────────────────────
    op.create_table(
        "company_features",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("feature_name", sa.String(64), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("signals", postgresql.JSONB, nullable=True),
        sa.Column("explanation", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_company_features_lookup", "company_features",
        ["tenant_id", "company_id", "feature_name"], unique=True,
    )

    # ── Funding Events ───────────────────────────────────────────
    op.create_table(
        "company_funding_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("round_type", sa.String(50), nullable=True),
        sa.Column("amount", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True, server_default="SAR"),
        sa.Column("date", sa.Date, nullable=True),
        sa.Column("investors", postgresql.JSONB, nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_funding_events_company", "company_funding_events",
        ["tenant_id", "company_id"],
    )

    # ── Job Postings ─────────────────────────────────────────────
    op.create_table(
        "company_job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("seniority", sa.String(50), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_job_postings_company", "company_job_postings",
        ["tenant_id", "company_id"],
    )
    op.create_index(
        "ix_job_postings_active", "company_job_postings",
        ["tenant_id", "company_id", "status"],
    )

    # ── Intent Signals ───────────────────────────────────────────
    op.create_table(
        "company_intent_rfps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("rfp_title", sa.String(500), nullable=True),
        sa.Column("rfp_number", sa.String(100), nullable=True),
        sa.Column("value", sa.Float, nullable=True),
        sa.Column("agency", sa.String(200), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_intent_rfps_company", "company_intent_rfps",
        ["tenant_id", "company_id"],
    )

    op.create_table(
        "company_intent_visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("page_url", sa.String(1000), nullable=True),
        sa.Column("page_title", sa.String(500), nullable=True),
        sa.Column("referrer", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("visited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_intent_visits_company", "company_intent_visits",
        ["tenant_id", "company_id"],
    )
    op.create_index(
        "ix_intent_visits_time", "company_intent_visits",
        ["visited_at"],
    )

    op.create_table(
        "company_intent_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=True),
        sa.Column("content_title", sa.String(500), nullable=True),
        sa.Column("content_url", sa.String(1000), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_intent_content_company", "company_intent_content",
        ["tenant_id", "company_id"],
    )

    op.create_table(
        "company_intent_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_title", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("last_interaction", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interaction_type", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_intent_contacts_company", "company_intent_contacts",
        ["tenant_id", "company_id"],
    )

    # ── Products ─────────────────────────────────────────────────
    op.create_table(
        "company_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("price", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True, server_default="SAR"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_products_company", "company_products",
        ["tenant_id", "company_id"],
    )

    # ── Deals ─────────────────────────────────────────────────────
    op.create_table(
        "company_deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("deal_name", sa.String(255), nullable=True),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(10), nullable=True, server_default="SAR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("probability", sa.Float, nullable=True),
        sa.Column("expected_close_date", sa.Date, nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_deals_company", "company_deals",
        ["tenant_id", "company_id"],
    )
    op.create_index(
        "ix_deals_status", "company_deals",
        ["tenant_id", "status"],
    )

    # ── Payments ──────────────────────────────────────────────────
    op.create_table(
        "company_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column("invoice_number", sa.String(100), nullable=True),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(10), nullable=True, server_default="SAR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("payment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_payments_company", "company_payments",
        ["tenant_id", "company_id"],
    )
    op.create_index(
        "ix_payments_status", "company_payments",
        ["tenant_id", "company_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("company_payments")
    op.drop_table("company_deals")
    op.drop_table("company_products")
    op.drop_table("company_intent_contacts")
    op.drop_table("company_intent_content")
    op.drop_table("company_intent_visits")
    op.drop_table("company_intent_rfps")
    op.drop_table("company_job_postings")
    op.drop_table("company_funding_events")
    op.drop_index("ix_company_features_lookup", table_name="company_features")
    op.drop_table("company_features")
    op.drop_column("companies", "branch_count")
    op.drop_column("companies", "country")
    op.drop_column("companies", "industry")
    op.drop_column("companies", "linkedin_url")
    op.drop_column("companies", "employee_count_prev_year")
    op.drop_column("companies", "revenue_2yr_ago")
    op.drop_column("companies", "revenue_prev_year")
    op.drop_column("companies", "annual_revenue")
    op.drop_column("companies", "parent_company_id")
