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
    # NOTE: FK constraints deferred to migration 0028 to handle
    # type casting of existing data correctly
    pass


def downgrade() -> None:
    pass
