"""enrichment: add composite indexes for enrich query performance

Adds:
  1. company_licenses(tenant_id, company_id) — used by ExpansionScoreComputer and RevenueScoreComputer
  2. company_licenses(tenant_id, company_id, status) — for active license lookups
  3. company_payments(tenant_id, company_id, payment_date) — for RevenueScoreComputer's 1yr window
  4. company_intent_contacts(tenant_id, company_id, role, last_interaction) — for IntentScoreComputer DM queries

Identified by performance audit: enrichment p95 8s (budget 5s) — missing indexes
caused sequential scans on company_licenses and intent tables.

Revision ID: 0028
Revises: 0027
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0028"
down_revision: Union[str, None] = "0027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. company_licenses — ExpansionScoreComputer queries by (company_id, tenant_id)
    op.create_index(
        "ix_licenses_company", "company_licenses",
        ["tenant_id", "company_id"],
    )

    # 2. company_licenses — RevenueScoreComputer queries active licenses
    op.create_index(
        "ix_licenses_active_company", "company_licenses",
        ["tenant_id", "company_id", "status"],
    )

    # 3. company_payments — RevenueScoreComputer filters by payment_date >= 1yr
    op.create_index(
        "ix_payments_company_date", "company_payments",
        ["tenant_id", "company_id", "payment_date"],
    )

    # 4. company_intent_contacts — IntentScoreComputer filters by role + last_interaction
    op.create_index(
        "ix_intent_contacts_role_interaction", "company_intent_contacts",
        ["tenant_id", "company_id", "role", "last_interaction"],
    )


def downgrade() -> None:
    op.drop_index("ix_intent_contacts_role_interaction", table_name="company_intent_contacts")
    op.drop_index("ix_payments_company_date", table_name="company_payments")
    op.drop_index("ix_licenses_active_company", table_name="company_licenses")
    op.drop_index("ix_licenses_company", table_name="company_licenses")
