"""Agent Reach: persistent evidence + signals with RLS tenant isolation.

Two new tables store external intelligence gathered by Agent Reach:
- agent_evidence: raw evidence items (web pages, repos, profiles, etc.)
- agent_signals: derived signals (hiring, funding, expansion, etc.)

Both tables carry tenant_id for RLS isolation. Deduplication is handled
via a unique fingerprint on (tenant_id, company_name, source_url, evidence_type).
Freshness is enforced via a TTL index on collected_at.

Revision ID: j5k6l7m8n9o0
Revises: i3j4k5l6m7n8
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "j5k6l7m8n9o0"
down_revision = "i3j4k5l6m7n8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_evidence ─────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.create_table(
        "agent_evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("company_name", sa.String(500), nullable=False, index=True),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False, server_default=""),
        sa.Column("summary", sa.Text, nullable=False, server_default=""),
        sa.Column("raw_data", JSONB, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
    )

    # Dedup: one evidence item per (tenant, company, source_url, type)
    op.create_index(
        "ix_agent_evidence_dedup",
        "agent_evidence",
        ["tenant_id", "company_name", "source_url", "evidence_type"],
        unique=True,
    )

    # Freshness: TTL lookup for stale evidence pruning
    op.create_index(
        "ix_agent_evidence_freshness",
        "agent_evidence",
        ["tenant_id", "collected_at"],
    )

    # Company lookup
    op.create_index(
        "ix_agent_evidence_company",
        "agent_evidence",
        ["tenant_id", "company_name"],
    )

    # ── agent_signals ──────────────────────────────────────────────
    op.create_table(
        "agent_signals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("company_name", sa.String(500), nullable=False, index=True),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="low"),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("source_urls", JSONB, nullable=False, server_default="[]"),
        sa.Column("evidence_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default="{}"),
    )

    # Dedup: one signal per (tenant, company, type, title)
    op.create_index(
        "ix_agent_signals_dedup",
        "agent_signals",
        ["tenant_id", "company_name", "signal_type", "title"],
        unique=True,
    )

    # Freshness: TTL lookup
    op.create_index(
        "ix_agent_signals_freshness",
        "agent_signals",
        ["tenant_id", "detected_at"],
    )

    # Company lookup
    op.create_index(
        "ix_agent_signals_company",
        "agent_signals",
        ["tenant_id", "company_name"],
    )

    # ── RLS policies ───────────────────────────────────────────────
    op.execute("ALTER TABLE agent_evidence ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_agent_evidence ON agent_evidence "
        "USING ((tenant_id)::text = current_setting('app.tenant_id'::text, true)) "
        "WITH CHECK ((tenant_id)::text = current_setting('app.tenant_id'::text, true))"
    )
    op.execute("ALTER TABLE agent_evidence FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE agent_signals ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_agent_signals ON agent_signals "
        "USING ((tenant_id)::text = current_setting('app.tenant_id'::text, true)) "
        "WITH CHECK ((tenant_id)::text = current_setting('app.tenant_id'::text, true))"
    )
    op.execute("ALTER TABLE agent_signals FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_agent_signals ON agent_signals")
    op.execute("ALTER TABLE agent_signals NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agent_signals DISABLE ROW LEVEL SECURITY")
    op.drop_table("agent_signals")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_agent_evidence ON agent_evidence")
    op.execute("ALTER TABLE agent_evidence NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agent_evidence DISABLE ROW LEVEL SECURITY")
    op.drop_table("agent_evidence")
