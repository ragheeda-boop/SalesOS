"""DEC-130g / criterion 7.6 Slice 5g: live index/FK KEEP registers must stay.

Guards against silent reintroduction of remove_index / remove_fk proposals
for indexes and FKs already live in Postgres. No DROP without dedicated DEC.
"""

from __future__ import annotations

from app.database import Base
from app.alembic.env import _KEEP_EXPRESSION_INDEXES, include_object


def test_tenants_slug_dual_unique_matches_live():
    t = Base.metadata.tables["tenants"]
    uq_names = {c.name for c in t.constraints if c.name}
    ix_names = {i.name for i in t.indexes}
    assert "tenants_slug_key" in uq_names
    assert "ix_tenants_slug" in ix_names
    slug_ix = next(i for i in t.indexes if i.name == "ix_tenants_slug")
    assert slug_ix.unique is False


def test_users_email_dual_unique_matches_live():
    t = Base.metadata.tables["users"]
    uq_names = {c.name for c in t.constraints if c.name}
    ix_names = {i.name for i in t.indexes}
    assert "users_email_key" in uq_names
    assert "ix_users_email" in ix_names
    email_ix = next(i for i in t.indexes if i.name == "ix_users_email")
    assert email_ix.unique is False


def test_golden_records_tenant_fk_and_unique_cr():
    t = Base.metadata.tables["golden_records"]
    fks = {fk.parent.name for fk in t.foreign_keys}
    assert "tenant_id" in fks
    assert "ix_golden_records_tenant_cr" in {i.name for i in t.indexes}


def test_webhook_deliveries_subscription_fk_cascade():
    t = Base.metadata.tables["webhook_deliveries"]
    fk = next(fk for fk in t.foreign_keys if fk.parent.name == "subscription_id")
    assert fk.ondelete == "CASCADE"
    assert "ix_webhook_deliveries_status_retry" in {i.name for i in t.indexes}


def test_graph_nodes_search_expression_keep_skipped():
    assert "ix_graph_nodes_search" in _KEEP_EXPRESSION_INDEXES
    assert include_object(None, "ix_graph_nodes_search", "index", True, None) is False
    assert include_object(None, "ix_companies_tenant_cr", "index", True, None) is True


def test_vectors_core_uses_pgvector_standin():
    cols = Base.metadata.tables["vectors"].c
    assert cols["id"].type.__class__.__name__ in {"TEXT", "Text"}
    assert cols["embedding"].nullable is False
    assert cols["metadata"].nullable is False
