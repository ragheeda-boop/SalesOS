"""add foreign key constraints to feature store tables

Adds FK references from all company_* feature/enrichment tables
to tenants(id) and companies(id) with CASCADE DELETE behavior.

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FEATURE_TABLES = [
    "company_features",
    "company_funding_events",
    "company_job_postings",
    "company_news_mentions",
    "company_government_contracts",
    "company_patents",
    "company_social_media",
    "company_website_mentions",
    "company_regulatory_filings",
    "company_market_share",
    "company_supply_chain",
    "company_intent_rfps",
    "company_intent_visits",
    "company_intent_content",
    "company_intent_contacts",
    "company_products",
    "company_deals",
    "company_payments",
]

_ALLOWED_MIGRATION_TABLES = frozenset(FEATURE_TABLES)


def _validate_migration_table(name: str) -> str:
    if name not in _ALLOWED_MIGRATION_TABLES:
        raise ValueError(f"Invalid migration table: {name}")
    return name


def upgrade() -> None:
    for table in FEATURE_TABLES:
        safe_table = _validate_migration_table(table)
        op.execute(f"""
            ALTER TABLE {safe_table}
            ADD CONSTRAINT fk_{table}_tenant
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            ON DELETE CASCADE
        """)
        op.execute(f"""
            ALTER TABLE {safe_table}
            ADD CONSTRAINT fk_{table}_company
            FOREIGN KEY (company_id) REFERENCES companies(id)
            ON DELETE CASCADE
        """)


def downgrade() -> None:
    for table in FEATURE_TABLES:
        safe_table = _validate_migration_table(table)
        op.execute(f"ALTER TABLE {safe_table} DROP CONSTRAINT IF EXISTS fk_{table}_company")
        op.execute(f"ALTER TABLE {safe_table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant")
