"""enrichment: add composite indexes for enrich query performance

Adds:
  1. licenses(company_id) — used by ExpansionScoreComputer and RevenueScoreComputer
  2. company_payments(tenant_id, company_id, payment_date) — for RevenueScoreComputer's 1yr window
  3. company_intent_contacts(tenant_id, company_id, role, last_interaction) — for IntentScoreComputer DM queries

Identified by performance audit: enrichment p95 8s (budget 5s) — missing indexes
caused sequential scans on licenses and intent tables.

Revision ID: 0028
Revises: 0027
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0028"
down_revision: Union[str, None] = "0027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_has_column(table_name: str, column_name: str, bind) -> bool:
    insp = sa.inspect(bind)
    try:
        columns = [c["name"] for c in insp.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # 1. licenses — ExpansionScoreComputer queries by company_id
    #    licenses table may or may not have tenant_id (baseline table)
    if _table_has_column("licenses", "tenant_id", bind):
        op.create_index(
            "ix_licenses_company", "licenses",
            ["tenant_id", "company_id"],
        )
        op.create_index(
            "ix_licenses_active_company", "licenses",
            ["tenant_id", "company_id", "status"],
        )
    else:
        op.create_index(
            "ix_licenses_company", "licenses",
            ["company_id"],
        )

    # 2. company_payments — RevenueScoreComputer filters by payment_date >= 1yr
    if _table_has_column("company_payments", "tenant_id", bind):
        op.create_index(
            "ix_payments_company_date", "company_payments",
            ["tenant_id", "company_id", "payment_date"],
        )

    # 3. company_intent_contacts — IntentScoreComputer filters by role + last_interaction
    if _table_has_column("company_intent_contacts", "tenant_id", bind):
        op.create_index(
            "ix_intent_contacts_role_interaction", "company_intent_contacts",
            ["tenant_id", "company_id", "role", "last_interaction"],
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _table_has_column("company_intent_contacts", "tenant_id", bind):
        op.drop_index("ix_intent_contacts_role_interaction", table_name="company_intent_contacts")
    if _table_has_column("company_payments", "tenant_id", bind):
        op.drop_index("ix_payments_company_date", table_name="company_payments")

    if _table_has_column("licenses", "tenant_id", bind):
        op.drop_index("ix_licenses_active_company", table_name="licenses")
        op.drop_index("ix_licenses_company", table_name="licenses")
    else:
        op.drop_index("ix_licenses_company", table_name="licenses")
