"""baseline: initial schema for SalesOS

Creates all core tables matching SQLAlchemy models:
- audit.audit_log (for AuditTrail)
- domain_events (for PostgresEventStore)
- tenants, users (Identity module)
- sources, companies, branches, licenses, contacts (Company module)
- golden_records, entity_resolution_conflicts (Entity Resolution)

Revision ID: 0001
Revises: None
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ──────────────────────────────────────────────────
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "vector"'))

    # ── Schemas ─────────────────────────────────────────────────────
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS audit'))
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS identity'))
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS company'))
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS activity'))
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS crm'))

    op.execute(sa.text(
        "CREATE TEXT SEARCH CONFIGURATION arabic (COPY = pg_catalog.simple)"
    ))

    # ── Audit Log (audit.audit_log) ─────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changes", postgresql.JSONB, nullable=True),
        sa.Column("performed_by", sa.String(255), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        schema="audit",
    )
    op.create_index("ix_audit_log_entity", "audit_log",
                    ["entity_type", "entity_id"], schema="audit")
    op.create_index("ix_audit_log_tenant_performed", "audit_log",
                    ["tenant_id", sa.text("performed_at DESC")], schema="audit")

    # ── Domain Events (domain_events) ───────────────────────────────
    op.create_table(
        "domain_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("event_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("aggregate_id", sa.String(255), nullable=False, index=True),
        sa.Column("aggregate_type", sa.String(100), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("data", postgresql.JSONB, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
    )

    # ── Tenants ─────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("domain", sa.String(255), nullable=True, unique=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("settings", postgresql.JSONB, nullable=True),
        sa.Column("features", postgresql.JSONB, nullable=True),
        sa.Column("subscription_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # ── Users ───────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("full_name_ar", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("preferences", postgresql.JSONB, nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # ── Sources ─────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("ingestion_config", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    # ── Companies ───────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name_ar", sa.String(500), nullable=False),
        sa.Column("name_en", sa.String(500), nullable=True),
        sa.Column("cr_number", sa.String(50), nullable=False),
        sa.Column("cr_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("city", sa.String(200), nullable=True),
        sa.Column("region", sa.String(200), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("fax", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("capital", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True, server_default="SAR"),
        sa.Column("employees_count", sa.Integer, nullable=True),
        sa.Column("activity_description", sa.Text, nullable=True),
        sa.Column("activity_code", sa.String(50), nullable=True),
        sa.Column("isic_code", sa.String(20), nullable=True),
        sa.Column("isic_description", sa.String(500), nullable=True),
        sa.Column("legal_form", sa.String(100), nullable=True),
        sa.Column("incorporation_date", sa.Date, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("is_golden_record", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("confidence_score", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("source_ids", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_companies_cr_number", "companies", ["cr_number"])
    op.create_index("ix_companies_name_ar", "companies", ["name_ar"])
    op.create_index("ix_companies_status", "companies", ["status"])
    op.create_index("ix_companies_city", "companies", ["city"])
    op.create_index("ix_companies_tenant_cr", "companies",
                    ["tenant_id", "cr_number"], unique=True)

    # ── Branches ────────────────────────────────────────────────────
    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("name_ar", sa.String(500), nullable=False),
        sa.Column("name_en", sa.String(500), nullable=True),
        sa.Column("branch_number", sa.String(50), nullable=True),
        sa.Column("city", sa.String(200), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    # ── Licenses ────────────────────────────────────────────────────
    op.create_table(
        "licenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("license_number", sa.String(100), nullable=False),
        sa.Column("license_type", sa.String(100), nullable=False),
        sa.Column("license_type_ar", sa.String(200), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("issuing_authority", sa.String(200), nullable=True),
        sa.Column("issue_date", sa.Date, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("renewal_date", sa.Date, nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_licenses_license_number", "licenses", ["license_number"])

    # ── Contacts ────────────────────────────────────────────────────
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_ar", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("mobile", sa.String(50), nullable=True),
        sa.Column("position", sa.String(255), nullable=True),
        sa.Column("position_ar", sa.String(255), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    # ── Entity Resolution Tables ────────────────────────────────────
    op.create_table(
        "golden_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("cr_number", sa.String(50), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("data", postgresql.JSONB, nullable=False,
                  comment="All fields with provenance: {field: {value, source, confidence, timestamp}}"),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("source_ids", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_golden_records_tenant_cr", "golden_records",
                    ["tenant_id", "cr_number"], unique=True)

    op.create_table(
        "entity_resolution_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("golden_record_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("golden_records.id"), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("source_a_value", sa.Text, nullable=True),
        sa.Column("source_a_source", sa.String(100), nullable=False),
        sa.Column("source_b_value", sa.Text, nullable=True),
        sa.Column("source_b_source", sa.String(100), nullable=False),
        sa.Column("resolution_strategy", sa.String(50), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "entity_resolution_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("source_slug", sa.String(100), nullable=True),
        sa.Column("records_processed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("records_matched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("records_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("records_merged", sa.Integer, nullable=False, server_default="0"),
        sa.Column("confidence_threshold", sa.Float, nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("entity_resolution_log")
    op.drop_table("entity_resolution_conflicts")
    op.drop_index("ix_golden_records_tenant_cr", table_name="golden_records")
    op.drop_table("golden_records")
    op.drop_table("contacts")
    op.drop_index("ix_licenses_license_number", table_name="licenses")
    op.drop_table("licenses")
    op.drop_table("branches")
    op.drop_index("ix_companies_tenant_cr", table_name="companies")
    op.drop_index("ix_companies_city", table_name="companies")
    op.drop_index("ix_companies_status", table_name="companies")
    op.drop_index("ix_companies_name_ar", table_name="companies")
    op.drop_index("ix_companies_cr_number", table_name="companies")
    op.drop_table("companies")
    op.drop_table("sources")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
    op.drop_table("domain_events")
    op.drop_index("ix_audit_log_tenant_performed", table_name="audit_log", schema="audit")
    op.drop_index("ix_audit_log_entity", table_name="audit_log", schema="audit")
    op.drop_table("audit_log", schema="audit")
    op.execute(sa.text("DROP TEXT SEARCH CONFIGURATION IF EXISTS arabic"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS crm"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS activity"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS company"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS identity"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS audit"))
