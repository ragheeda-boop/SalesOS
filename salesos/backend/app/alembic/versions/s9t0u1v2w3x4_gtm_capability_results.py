"""Seismic: durable per-tenant GTM capability result records (CAP-096..CAP-104).

One table, capability-discriminated, stores the result records of the eight
STORY-11 GTM capabilities that were previously in-memory only:

  market_sizing (TAM/SAM/SOM), lead_discovery, lookalike, enrichment,
  verification, website_intelligence, outreach, sequence_definition,
  sequence_enrollment (CAP-096/097/098/099/100/101/103/104).

Each row carries the canonical result payload (the model's as_dict()) under
jsonb `payload` plus an envelope (capability, id, tenant_id, name,
schema_version, created_at, updated_at). Isolation follows the canonical
DEC-085 RLS shape used by icp_profiles (h2i3j4k5l6m8): ENABLE + tenant
policy + FORCE ROW LEVEL SECURITY, with the restricted runtime role granted
CRUD exactly like w6x7y8z9a0b1_tenant_ai_memory_persistence. The payload
also carries tenant_id/id for defence in depth.

Compute kernels stay in the pure engine modules; this table only persists
their produced result records.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "s9t0u1v2w3x4"
down_revision: str | None = "r4s5t6u7v8w9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABLE = "gtm_capability_results"
POLICY = "tenant_isolation_gtm_capability_results"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("capability", sa.String(64), primary_key=True),
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
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
    op.create_index(
        "ix_gtm_capability_results_tenant_capability",
        TABLE,
        ["tenant_id", "capability"],
    )
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {POLICY} ON {TABLE} "
        "USING ((tenant_id)::text = current_setting('app.tenant_id'::text, true)) "
        "WITH CHECK ((tenant_id)::text = current_setting('app.tenant_id'::text, true))"
    )
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
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
    op.execute(f"DROP POLICY IF EXISTS {POLICY} ON {TABLE}")
    op.execute(f"ALTER TABLE {TABLE} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_gtm_capability_results_tenant_capability", table_name=TABLE)
    op.drop_table(TABLE)