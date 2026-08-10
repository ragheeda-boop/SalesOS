"""Track F1: Company signals persistence — replace ad-hoc / transient signals.

Revision ID: c1d2e3f4a5b6
Revises: b0d0e0f0a0d0
Create Date: 2026-08-10

Creates company_signals with full lifecycle support:
- tenant_id (FK, NOT NULL) — tenant isolation
- company_id (FK, NOT NULL) — parent entity
- signal_type (NOT NULL) — expired, expiring_soon, expiring, stalled_pipeline, won_deals, no_contacts, no_branches, low_confidence, low_data_quality
- title, description — display fields
- severity (NOT NULL) — critical, high, medium, info, positive
- source — provenance (heuristic, enricher, manual, odoo)
- status — active, acknowledged, resolved, expired
- confidence_score — 0.0–1.0
- first_seen_at, last_seen_at — lifecycle tracking
- metadata — extensible JSONB
- dedup key: (tenant_id, company_id, signal_type) UNIQUE

RLS: Category A (direct tenant_id). FORCE ROW LEVEL SECURITY.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b0d0e0f0a0d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "company_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),

        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),

        sa.Column("source", sa.String(50), nullable=False, server_default="heuristic"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("confidence_score", sa.Float(), nullable=True),

        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Dedup: one active signal of each type per company per tenant
    op.execute(sa.text(
        "ALTER TABLE company_signals ADD CONSTRAINT uq_company_signal_type "
        "UNIQUE (tenant_id, company_id, signal_type)"
    ))

    # Performance indexes
    op.execute(sa.text(
        "CREATE INDEX ix_company_signals_tenant_company "
        "ON company_signals (tenant_id, company_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_company_signals_status "
        "ON company_signals (tenant_id, status)"
    ))
    op.execute(sa.text(
        "CREATE INDEX ix_company_signals_type "
        "ON company_signals (signal_type)"
    ))

    # RLS
    op.execute(sa.text("ALTER TABLE company_signals ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(
        "ALTER TABLE company_signals FORCE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(generate_policy_sql("company_signals")))


def downgrade() -> None:
    op.drop_table("company_signals")
