"""performance: add missing indexes for entity_resolution, timeline, and feature queries

Adds:
  1. entity_resolution_conflicts(golden_record_id, status) — composite for conflict lookups
  2. timeline_entries(actor) — for actor-based timeline queries
  3. timeline_entries(tenant_id, created_at) — for recent timeline queries

Identified by performance audit: enrichment p95 8s (budget 5s) and timeline p95 300ms (budget 300ms).

Revision ID: 0027
Revises: 0026
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0027"
down_revision: Union[str, None] = "0026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Entity resolution conflicts — conflict queries filter by golden_record_id AND status
    op.create_index(
        "ix_conflicts_golden_status", "entity_resolution_conflicts",
        ["golden_record_id", "status"],
    )

    # 2. Timeline — actor-based lookups (used by get_by_actor and query with actor_id filter)
    op.create_index(
        "ix_timeline_actor", "timeline_entries", ["actor"],
    )

    # 3. Timeline — recent timeline queries filter by tenant_id + order by created_at desc
    op.create_index(
        "ix_timeline_tenant_created", "timeline_entries",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_timeline_tenant_created", table_name="timeline_entries")
    op.drop_index("ix_timeline_actor", table_name="timeline_entries")
    op.drop_index("ix_conflicts_golden_status", table_name="entity_resolution_conflicts")
