"""Persist tenant-scoped commercial relationship edges with lifecycle evidence.

Revision ID: u1v2w3x4y5z6
Revises: s9t0u1v2w3x4

Typed person<->person and person<->company edges (reports_to, influences,
champion_for, blocks, introduced_by) used by the Commercial Relationship
Model. Each row carries a lifecycle: observed_at, superseded_at, basis,
confidence and evidence. Isolation follows the canonical DEC-085 RLS shape:
ENABLE + tenant policy + FORCE ROW LEVEL SECURITY, with the restricted
runtime role granted CRUD as in s9t0u1v2w3x4.

opportunity_contacts remains the existing bounded stakeholder slice; this
table is the general relationship-graph store and does not replace it.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.alembic.lib.rls import generate_policy_sql

revision: str = "u1v2w3x4y5z6"
down_revision: str | None = "s9t0u1v2w3x4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "commercial_relationship_edges"
POLICY = "tenant_isolation_commercial_relationship_edges"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("edge_type", sa.String(32), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("basis", sa.String(64), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    # One ACTIVE edge per (edge_type, source, target) within a tenant.
    # Superseding the current row releases the slot so the lifecycle can
    # record a replacement edge arriving later.
    op.execute(
        sa.text(
            f"CREATE UNIQUE INDEX ux_relationship_edge_active ON {TABLE} "
            "(tenant_id, edge_type, source_type, source_id, target_type, target_id) "
            "WHERE superseded_at IS NULL"
        )
    )
    op.create_index(
        "ix_relationship_edges_tenant_source",
        TABLE,
        ["tenant_id", "source_type", "source_id"],
    )
    op.create_index(
        "ix_relationship_edges_tenant_target",
        TABLE,
        ["tenant_id", "target_type", "target_id"],
    )
    op.create_index(
        "ix_relationship_edges_tenant_active",
        TABLE,
        ["tenant_id", "edge_type", "superseded_at"],
    )
    for statement in generate_policy_sql(TABLE).strip().split(";\n"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))
    op.execute(sa.text("REVOKE ALL ON commercial_relationship_edges FROM PUBLIC"))
    op.execute(
        sa.text(
            "DO $grant$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON "
            f"{TABLE} TO salesos_app; "
            "END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DO $revoke$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN "
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON {TABLE} FROM salesos_app; "
            "END IF; END $revoke$;"
        )
    )
    op.execute(sa.text(f'DROP POLICY IF EXISTS "{POLICY}" ON "{TABLE}"'))
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" DISABLE ROW LEVEL SECURITY'))
    op.drop_index("ix_relationship_edges_tenant_active", table_name=TABLE)
    op.drop_index("ix_relationship_edges_tenant_target", table_name=TABLE)
    op.drop_index("ix_relationship_edges_tenant_source", table_name=TABLE)
    op.execute(sa.text("DROP INDEX IF EXISTS ux_relationship_edge_active"))
    op.drop_table(TABLE)