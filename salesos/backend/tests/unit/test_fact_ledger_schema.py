"""Offline contract tests for the governed canonical fact ledger schema."""

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.modules.facts.models import (
    CanonicalFact,
    CanonicalFactEvent,
    EvidenceRecord,
    FactEvidence,
)


def test_ledger_tables_are_tenant_scoped_and_registered() -> None:
    expected = {
        "evidence_records",
        "canonical_facts",
        "fact_evidence",
        "canonical_fact_events",
    }
    assert expected <= set(CanonicalFact.metadata.tables)
    for name in expected:
        table = CanonicalFact.metadata.tables[name]
        assert "tenant_id" in table.c
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        assert "tenant_id UUID NOT NULL" in ddl


def test_fact_schema_has_fail_closed_states_and_dismissal_guard() -> None:
    table = CanonicalFact.__table__
    assert any(c.name == "ck_canonical_facts_subject_type" for c in table.constraints)
    assert any(c.name == "ck_canonical_facts_status" for c in table.constraints)
    index_names = {index.name for index in table.indexes}
    assert "uq_canonical_facts_open_value" in index_names
    assert "uq_canonical_facts_dismissed_value" in index_names


def test_fact_evidence_and_events_enforce_same_tenant_references() -> None:
    mapping_fks = {fk.name for fk in FactEvidence.__table__.foreign_key_constraints}
    event_fks = {fk.name for fk in CanonicalFactEvent.__table__.foreign_key_constraints}
    assert "fk_fact_evidence_fact_tenant" in mapping_fks
    assert "fk_fact_evidence_evidence_tenant" in mapping_fks
    assert "fk_canonical_fact_events_fact_tenant" in event_fks
    assert any(
        fk.name == "fk_canonical_facts_supersedes_tenant"
        for fk in CanonicalFact.__table__.foreign_key_constraints
    )
    assert "uq_evidence_records_id_tenant" in {c.name for c in EvidenceRecord.__table__.constraints}
    assert "request_fingerprint" in CanonicalFact.__table__.c
