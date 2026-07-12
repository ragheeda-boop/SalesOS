"""add foreign key constraints to commercial domain tables

Adds FK references for:
  - commercial_opportunities → tenants(id), companies(id)
  - commercial_quotes       → commercial_opportunities(id), tenants(id), companies(id)
  - commercial_contracts    → commercial_opportunities(id), commercial_quotes(id), tenants(id)
  - commercial_proposals    → commercial_opportunities(id), commercial_quotes(id), tenants(id)
  - emails                  → commercial_opportunities(id), companies(id), tenants(id)
  - meetings                → commercial_opportunities(id), companies(id), tenants(id)
  - commercial_activities   → commercial_activity_sessions(id), tenants(id)

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── commercial_opportunities ──────────────────────────────────
    op.create_foreign_key(
        "fk_commercial_opportunities_tenant",
        "commercial_opportunities", "tenants",
        ["tenant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_commercial_opportunities_company",
        "commercial_opportunities", "companies",
        ["company_id"], ["id"],
        ondelete="CASCADE",
    )

    # ── commercial_quotes ─────────────────────────────────────────
    op.create_foreign_key(
        "fk_commercial_quotes_tenant",
        "commercial_quotes", "tenants",
        ["tenant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_commercial_quotes_opportunity",
        "commercial_quotes", "commercial_opportunities",
        ["opportunity_id"], ["id"],
        ondelete="CASCADE",
    )

    # ── commercial_contracts ──────────────────────────────────────
    op.create_foreign_key(
        "fk_commercial_contracts_tenant",
        "commercial_contracts", "tenants",
        ["tenant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_commercial_contracts_opportunity",
        "commercial_contracts", "commercial_opportunities",
        ["opportunity_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_commercial_contracts_quote",
        "commercial_contracts", "commercial_quotes",
        ["quote_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── commercial_proposals ──────────────────────────────────────
    op.create_foreign_key(
        "fk_commercial_proposals_tenant",
        "commercial_proposals", "tenants",
        ["tenant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_commercial_proposals_opportunity",
        "commercial_proposals", "commercial_opportunities",
        ["opportunity_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_commercial_proposals_quote",
        "commercial_proposals", "commercial_quotes",
        ["quote_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── emails ────────────────────────────────────────────────────
    op.create_foreign_key(
        "fk_emails_tenant",
        "emails", "tenants",
        ["tenant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_emails_opportunity",
        "emails", "commercial_opportunities",
        ["opportunity_id"], ["id"],
        ondelete="CASCADE",
    )

    # ── meetings ──────────────────────────────────────────────────
    op.create_foreign_key(
        "fk_meetings_tenant",
        "meetings", "tenants",
        ["tenant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_meetings_opportunity",
        "meetings", "commercial_opportunities",
        ["opportunity_id"], ["id"],
        ondelete="CASCADE",
    )

    # ── commercial_activities ─────────────────────────────────────
    # session_id FK to commercial_activity_sessions already exists
    # Add tenant_id column and FK
    op.add_column(
        "commercial_activities",
        sa.Column("tenant_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_commercial_activities_tenant",
        "commercial_activities", "tenants",
        ["tenant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_commercial_activities_tenant",
        "commercial_activities",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_commercial_activities_tenant", table_name="commercial_activities")
    op.drop_constraint("fk_commercial_activities_tenant", "commercial_activities", type_="foreignkey")
    op.drop_column("commercial_activities", "tenant_id")

    op.drop_constraint("fk_meetings_opportunity", "meetings", type_="foreignkey")
    op.drop_constraint("fk_meetings_tenant", "meetings", type_="foreignkey")

    op.drop_constraint("fk_emails_opportunity", "emails", type_="foreignkey")
    op.drop_constraint("fk_emails_tenant", "emails", type_="foreignkey")

    op.drop_constraint("fk_commercial_proposals_quote", "commercial_proposals", type_="foreignkey")
    op.drop_constraint("fk_commercial_proposals_opportunity", "commercial_proposals", type_="foreignkey")
    op.drop_constraint("fk_commercial_proposals_tenant", "commercial_proposals", type_="foreignkey")

    op.drop_constraint("fk_commercial_contracts_quote", "commercial_contracts", type_="foreignkey")
    op.drop_constraint("fk_commercial_contracts_opportunity", "commercial_contracts", type_="foreignkey")
    op.drop_constraint("fk_commercial_contracts_tenant", "commercial_contracts", type_="foreignkey")

    op.drop_constraint("fk_commercial_quotes_opportunity", "commercial_quotes", type_="foreignkey")
    op.drop_constraint("fk_commercial_quotes_tenant", "commercial_quotes", type_="foreignkey")

    op.drop_constraint("fk_commercial_opportunities_company", "commercial_opportunities", type_="foreignkey")
    op.drop_constraint("fk_commercial_opportunities_tenant", "commercial_opportunities", type_="foreignkey")
