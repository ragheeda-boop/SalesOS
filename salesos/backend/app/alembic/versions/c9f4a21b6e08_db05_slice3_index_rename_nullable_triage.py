"""DB-05 Slice 3: index rename + nullable triage (additive).

Revision ID: c9f4a21b6e08
Revises: b7e2f65a3f07
Create Date: 2026-08-01

DEC-122 / DB-05 Slice 3 (R-20 / DEC-111 P1):
  - Free commercial_opportunities index names that collide with revenue
    opportunities (0007 created ix_opportunities_* on commercial table)
  - Rename ix_rev_* → ix_* on opportunities/tasks (ORM match)
  - Rename webhook/scheduled_jobs index names to ORM index=True defaults
  - Drop redundant workflow short-name indexes when *_id twins already exist
  - Additive CREATE for missing notification composites + tasks.company_id
    + commercial owner index if missing

Does NOT DROP companies dead columns (STOP — see DEC-122).
Does NOT ENABLE RLS on deferred-8.
Does NOT touch get_db() / DEC-085 set_config.
Idempotent: rename/create/drop only when source/target state matches.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9f4a21b6e08"
down_revision: Union[str, None] = "b7e2f65a3f07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Must run BEFORE revenue opportunities renames — schema-global index names.
# commercial ORM wants ix_commercial_opps_*; 0007 used ix_opportunities_*.
_COMMERCIAL_FREE_RENAMES: list[tuple[str, str]] = [
    ("ix_opportunities_tenant_stage", "ix_commercial_opps_tenant_stage"),
    ("ix_opportunities_tenant_status", "ix_commercial_opps_tenant_status"),
]

# (old_name, new_name)
_INDEX_RENAMES: list[tuple[str, str]] = [
    ("ix_rev_opportunities_tenant_id", "ix_opportunities_tenant_id"),
    ("ix_rev_opportunities_tenant_stage", "ix_opportunities_tenant_stage"),
    ("ix_rev_opportunities_company", "ix_opportunities_company"),
    ("ix_rev_tasks_tenant_id", "ix_tasks_tenant_id"),
    ("ix_rev_tasks_tenant_priority", "ix_tasks_tenant_priority"),
    ("ix_rev_tasks_assignee_completed", "ix_tasks_assignee_completed"),
    ("ix_webhook_subscriptions_tenant", "ix_webhook_subscriptions_tenant_id"),
    ("ix_webhook_deliveries_subscription", "ix_webhook_deliveries_subscription_id"),
    ("ix_scheduled_jobs_next_run", "ix_scheduled_jobs_next_run_at"),
]

# Drop legacy short names only when the ORM-aligned twin already exists.
# (table, short_name, keep_name, columns_for_downgrade_recreate)
_DUPLICATE_SHORT_INDEXES: list[tuple[str, str, str, list[str]]] = [
    ("workflow_definitions", "ix_workflow_definitions_tenant", "ix_workflow_definitions_tenant_id", ["tenant_id"]),
    ("workflow_executions", "ix_workflow_executions_tenant", "ix_workflow_executions_tenant_id", ["tenant_id"]),
    ("workflow_executions", "ix_workflow_executions_workflow", "ix_workflow_executions_workflow_id", ["workflow_id"]),
]

# Additive creates matching ORM __table_args__ / index=True
_CREATE_INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_notifications_user_read", "notifications", ["user_id", "read", "created_at"]),
    ("ix_notifications_tenant_type", "notifications", ["tenant_id", "type"]),
    ("ix_tasks_company_id", "tasks", ["company_id"]),
    ("ix_commercial_opps_owner", "commercial_opportunities", ["owner_id"]),
]


def _index_exists(conn, name: str) -> bool:
    row = conn.execute(
        sa.text("SELECT 1 FROM pg_class WHERE relkind = 'i' AND relname = :n"),
        {"n": name},
    ).fetchone()
    return row is not None


def _rename_index_if_needed(conn, old: str, new: str) -> None:
    if _index_exists(conn, new):
        return
    if _index_exists(conn, old):
        op.execute(sa.text(f'ALTER INDEX "{old}" RENAME TO "{new}"'))


def upgrade() -> None:
    conn = op.get_bind()

    for old, new in _COMMERCIAL_FREE_RENAMES:
        _rename_index_if_needed(conn, old, new)

    for old, new in _INDEX_RENAMES:
        _rename_index_if_needed(conn, old, new)

    for table, short_name, keep_name, _cols in _DUPLICATE_SHORT_INDEXES:
        if _index_exists(conn, short_name) and _index_exists(conn, keep_name):
            op.drop_index(short_name, table_name=table)

    for name, table, cols in _CREATE_INDEXES:
        if not _index_exists(conn, name):
            op.create_index(name, table, cols)


def downgrade() -> None:
    conn = op.get_bind()

    for name, table, _cols in reversed(_CREATE_INDEXES):
        if _index_exists(conn, name):
            op.drop_index(name, table_name=table)

    for table, short_name, keep_name, cols in reversed(_DUPLICATE_SHORT_INDEXES):
        if not _index_exists(conn, short_name) and _index_exists(conn, keep_name):
            op.create_index(short_name, table, cols)

    for old, new in reversed(_INDEX_RENAMES):
        _rename_index_if_needed(conn, new, old)

    for old, new in reversed(_COMMERCIAL_FREE_RENAMES):
        _rename_index_if_needed(conn, new, old)
