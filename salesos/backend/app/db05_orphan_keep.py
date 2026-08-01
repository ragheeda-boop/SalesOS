"""DEC-130f / criterion 7.6 Slice 5f — metadata KEEP for live orphan tables.

These tables exist in Postgres (migrations 0002–0015 / 0003–0004) and are used
via raw SQL / feature-store paths, but have no Declarative ORM on shared Base.
Registering Core ``Table`` stubs stops ``alembic check`` from proposing
``remove_table`` DROP. Disposition = KEEP. **No DROP without a dedicated DEC.**
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.types import UserDefinedType

# Private MetaData — copied onto Base.metadata via register_orphan_keep_tables().
_orphan_md = MetaData()

# Authoritative orphan KEEP inventory (DEC-130b residual → DEC-130f register).
ORPHAN_KEEP_TABLES: frozenset[str] = frozenset(
    {
        "company_funding_events",
        "company_payments",
        "company_job_postings",
        "company_intent_contacts",
        "company_intent_visits",
        "company_intent_rfps",
        "company_intent_content",
        "company_products",
        "company_deals",
        "company_policies",
        "decisions",
        "decision_feedback_loop",
        "rag_documents",
        "rag_document_chunks",
        "graph_nodes",
    }
)


class _PgVector(UserDefinedType):
    """pgvector metadata stand-in — compare_against_backend silences DROP/ALTER."""

    cache_ok = True

    def __init__(self, dim: int = 3072) -> None:
        self.dim = dim

    def get_col_spec(self, **_kw: Any) -> str:
        return f"vector({self.dim})"

    def compare_against_backend(self, _dialect: Any, _conn_type: Any) -> bool:
        return True


# ── Feature-store enrichment (0002) ─────────────────────────────────────────

Table(
    "company_funding_events",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("round_type", String(50), nullable=True),
    Column("amount", Float, nullable=True),
    Column("currency", String(10), nullable=True),
    Column("date", Date, nullable=True),
    Column("investors", JSONB, nullable=True),
    Column("source", String(100), nullable=True),
    Column("source_url", String(500), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_funding_events_company", "tenant_id", "company_id"),
)

Table(
    "company_job_postings",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("title", String(255), nullable=False),
    Column("role", String(100), nullable=True),
    Column("seniority", String(50), nullable=True),
    Column("department", String(100), nullable=True),
    Column("location", String(200), nullable=True),
    Column("status", String(20), nullable=False),
    Column("posted_at", DateTime(timezone=True), nullable=True),
    Column("source_url", String(500), nullable=True),
    Column("source", String(100), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_job_postings_company", "tenant_id", "company_id"),
    Index("ix_job_postings_active", "tenant_id", "company_id", "status"),
)

Table(
    "company_intent_rfps",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("rfp_title", String(500), nullable=True),
    Column("rfp_number", String(100), nullable=True),
    Column("value", Float, nullable=True),
    Column("agency", String(200), nullable=True),
    Column("status", String(50), nullable=True),
    Column("detected_at", DateTime(timezone=True), nullable=False),
    Column("source_url", String(500), nullable=True),
    Column("source", String(100), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_intent_rfps_company", "tenant_id", "company_id"),
)

Table(
    "company_intent_visits",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("page_url", String(1000), nullable=True),
    Column("page_title", String(500), nullable=True),
    Column("referrer", String(500), nullable=True),
    Column("ip_address", String(50), nullable=True),
    Column("user_agent", String(500), nullable=True),
    Column("visited_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_intent_visits_company", "tenant_id", "company_id"),
    Index("ix_intent_visits_time", "visited_at"),
)

Table(
    "company_intent_content",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("content_type", String(50), nullable=True),
    Column("content_title", String(500), nullable=True),
    Column("content_url", String(1000), nullable=True),
    Column("category", String(100), nullable=True),
    Column("consumed_at", DateTime(timezone=True), nullable=False),
    Column("source", String(100), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_intent_content_company", "tenant_id", "company_id"),
)

Table(
    "company_intent_contacts",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("contact_name", String(255), nullable=True),
    Column("contact_title", String(255), nullable=True),
    Column("role", String(50), nullable=True),
    Column("email", String(255), nullable=True),
    Column("phone", String(50), nullable=True),
    Column("last_interaction", DateTime(timezone=True), nullable=True),
    Column("interaction_type", String(50), nullable=True),
    Column("notes", Text, nullable=True),
    Column("source", String(100), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_intent_contacts_company", "tenant_id", "company_id"),
    Index(
        "ix_intent_contacts_role_interaction",
        "tenant_id",
        "company_id",
        "role",
        "last_interaction",
    ),
)

Table(
    "company_products",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("name", String(255), nullable=False),
    Column("category", String(100), nullable=True),
    Column("description", Text, nullable=True),
    Column("price", Float, nullable=True),
    Column("currency", String(10), nullable=True),
    Column("is_active", Boolean, nullable=False),
    Column("source", String(100), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_products_company", "tenant_id", "company_id"),
)

Table(
    "company_deals",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("deal_name", String(255), nullable=True),
    Column("amount", Float, nullable=False),
    Column("currency", String(10), nullable=True),
    Column("status", String(50), nullable=False),
    Column("stage", String(50), nullable=True),
    Column("probability", Float, nullable=True),
    Column("expected_close_date", Date, nullable=True),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Column("owner", String(255), nullable=True),
    Column("notes", Text, nullable=True),
    Column("source", String(100), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_deals_company", "tenant_id", "company_id"),
    Index("ix_deals_status", "tenant_id", "status"),
)

Table(
    "company_payments",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("invoice_number", String(100), nullable=True),
    Column("amount", Float, nullable=False),
    Column("currency", String(10), nullable=True),
    Column("status", String(50), nullable=False),
    Column("due_date", Date, nullable=True),
    Column("payment_date", DateTime(timezone=True), nullable=True),
    Column("payment_method", String(50), nullable=True),
    Column("notes", Text, nullable=True),
    Column("source", String(100), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_payments_company", "tenant_id", "company_id"),
    Index("ix_payments_status", "tenant_id", "company_id", "status"),
    Index("ix_payments_company_date", "tenant_id", "company_id", "payment_date"),
)

# ── Decision engine (0003) ──────────────────────────────────────────────────

Table(
    "decisions",
    _orphan_md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("decision_id", String(64), nullable=False, unique=True),
    Column("company_id", String(36), nullable=False),
    Column("tenant_id", String(36), nullable=False),
    Column("decision_type", String(50), nullable=False),
    Column("priority", Integer, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("expected_revenue", Float, nullable=True),
    Column("expected_probability", Float, nullable=True),
    Column("reasoning", Text, nullable=True),
    Column("evidence", JSONB, nullable=True),
    Column("supporting_features", JSONB, nullable=True),
    Column("context_snapshot", JSONB, nullable=True),
    Column("required_actions", JSONB, nullable=True),
    Column("blocked_by", JSONB, nullable=True),
    Column("status", String(20), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("executed_at", DateTime(timezone=True), nullable=True),
    Index("ix_decisions_company", "tenant_id", "company_id"),
    Index("ix_decisions_status", "tenant_id", "status"),
    Index("ix_decisions_created", text("created_at DESC")),
)

Table(
    "decision_feedback_loop",
    _orphan_md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("decision_id", String(64), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("tenant_id", String(36), nullable=False),
    Column("user_accepted", Boolean, nullable=False),
    Column("executed", Boolean, nullable=False),
    Column("outcome", String(20), nullable=True),
    Column("outcome_value", Float, nullable=True),
    Column("learning", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_feedback_decision", "decision_id"),
    Index("ix_feedback_company", "tenant_id", "company_id"),
)

Table(
    "company_policies",
    _orphan_md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tenant_id", String(36), nullable=False),
    Column("company_id", String(36), nullable=False),
    Column("policy_name", String(100), nullable=False),
    Column("policy_type", String(50), nullable=False),
    Column("action", String(20), nullable=False),
    Column("reason", Text, nullable=True),
    Column("severity", Integer, nullable=False),
    Column("is_active", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index(
        "ix_policies_company",
        "tenant_id",
        "company_id",
        "policy_name",
        unique=True,
    ),
)

# ── Knowledge graph nodes (0004) — edges already registered DEC-130b ────────

Table(
    "graph_nodes",
    _orphan_md,
    Column("id", String(64), primary_key=True),
    Column("tenant_id", String(36), nullable=False, index=True),
    Column("labels", ARRAY(String(50)), nullable=False),
    Column("properties", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    # Expression GIN ix_graph_nodes_search is live; not mirrored (expression).
)

# ── RAG (0015) ──────────────────────────────────────────────────────────────

Table(
    "rag_documents",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", String(36), nullable=False),
    Column("source_type", String(50), nullable=False),
    Column("source_id", String(255), nullable=False),
    Column("title", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("metadata", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("idx_rag_chunks_tenant", "tenant_id"),
)

Table(
    "rag_document_chunks",
    _orphan_md,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("content", Text, nullable=False),
    Column("chunk_index", Integer, nullable=False),
    Column("metadata", JSONB, nullable=False),
    Column("embedding", _PgVector(3072), nullable=True),
    Index("idx_rag_chunks_document", "document_id"),
)


def register_orphan_keep_tables(target_metadata: MetaData) -> None:
    """Copy orphan KEEP Table stubs onto shared Base.metadata (idempotent).

    Parent tables first so FK copies (rag_document_chunks → rag_documents) resolve.
    """
    _order = (
        "company_funding_events",
        "company_job_postings",
        "company_intent_rfps",
        "company_intent_visits",
        "company_intent_content",
        "company_intent_contacts",
        "company_products",
        "company_deals",
        "company_payments",
        "decisions",
        "decision_feedback_loop",
        "company_policies",
        "graph_nodes",
        "rag_documents",
        "rag_document_chunks",
    )
    assert set(_order) == ORPHAN_KEEP_TABLES
    for name in _order:
        tbl = _orphan_md.tables[name]
        if tbl.key not in target_metadata.tables:
            tbl.to_metadata(target_metadata)
