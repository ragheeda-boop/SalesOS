"""Unit tests for the Commercial Relationship Model (pure model contract).

Validates the typed edge vocabulary, endpoint type rules, self-loop
rejection, confidence bounds, evidence shape and id/tenant normalization —
all without a database.
"""

from __future__ import annotations

import pytest

from app.modules.relationships.models import (
    EDGE_TYPE_SET,
    ENDPOINT_TYPE_SET,
    RELATIONSHIP_EDGE_TYPES,
    RelationshipError,
    is_endpoint_type,
    normalize_edge,
)

TENANT_A = "a0000000-0000-4000-a000-000000000001"
TENANT_B = "b0000000-0000-4000-b000-000000000002"


class TestEdgeVocabulary:
    def test_taxonomy_is_bounded_and_exact(self):
        assert RELATIONSHIP_EDGE_TYPES == (
            "reports_to",
            "influences",
            "champion_for",
            "blocks",
            "introduced_by",
        )

    def test_known_basis(self):
        from app.modules.relationships.models import known_basis

        assert known_basis("source_assignment")
        assert known_basis("title_keyword")
        assert known_basis("org_structure")
        assert known_basis("manual")
        assert not known_basis("made_up_basis")

    def test_endpoint_types(self):
        assert is_endpoint_type("person")
        assert is_endpoint_type("company")
        assert not is_endpoint_type("account")

    def test_all_edge_types_accept_valid_person_pairs(self):
        for etype in RELATIONSHIP_EDGE_TYPES:
            edge = normalize_edge(
                tenant_id=TENANT_A,
                edge_type=etype,
                source_type="person",
                source_id="p-11111111",
                target_type="person",
                target_id="p-22222222",
            )
            assert edge.edge_type == etype


class TestValidation:
    def test_rejects_unknown_edge_type(self):
        with pytest.raises(RelationshipError, match="invalid edge_type"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="reportsInto",
                source_type="person",
                source_id="p-1",
                target_type="person",
                target_id="p-2",
            )

    def test_rejects_unknown_source_type(self):
        with pytest.raises(RelationshipError, match="invalid source_type"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="influences",
                source_type="contact",
                source_id="p-1",
                target_type="person",
                target_id="p-2",
            )

    def test_rejects_unknown_target_type(self):
        with pytest.raises(RelationshipError, match="invalid target_type"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="champion_for",
                source_type="person",
                source_id="p-1",
                target_type="org",
                target_id="p-2",
            )

    def test_rejects_self_loop(self):
        with pytest.raises(RelationshipError, match="self loop"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="reports_to",
                source_type="person",
                source_id="p-11111111",
                target_type="person",
                target_id="p-11111111",
            )

    def test_rejects_empty_ids(self):
        with pytest.raises(RelationshipError, match="source_id required"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="influences",
                source_type="person",
                source_id="",
                target_type="person",
                target_id="p-22222222",
            )

    def test_rejects_overlong_id(self):
        with pytest.raises(RelationshipError, match="exceeds 36"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="influences",
                source_type="person",
                source_id="x" * 37,
                target_type="person",
                target_id="p-22222222",
            )

    def test_rejects_bad_confidence(self):
        with pytest.raises(RelationshipError, match="confidence"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="influences",
                source_type="person",
                source_id="p-1",
                target_type="person",
                target_id="p-2",
                confidence=1.5,
            )

    def test_rejects_negative_confidence(self):
        with pytest.raises(RelationshipError, match="confidence"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="influences",
                source_type="person",
                source_id="p-1",
                target_type="person",
                target_id="p-2",
                confidence=-0.1,
            )

    def test_rejects_non_dict_evidence(self):
        with pytest.raises(RelationshipError, match="evidence"):
            normalize_edge(
                tenant_id=TENANT_A,
                edge_type="influences",
                source_type="person",
                source_id="p-1",
                target_type="person",
                target_id="p-2",
                evidence=["not-a-dict"],
            )


class TestNormalization:
    def test_tenant_id_normalized_to_uuid_canonical(self):
        edge = normalize_edge(
            tenant_id="A0000000-0000-4000-A000-000000000001",
            edge_type="reports_to",
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-2",
        )
        assert edge.tenant_id == TENANT_A

    def test_rejects_non_uuid_tenant(self):
        with pytest.raises(RelationshipError, match="tenant_id"):
            normalize_edge(
                tenant_id="not-a-uuid",
                edge_type="reports_to",
                source_type="person",
                source_id="p-1",
                target_type="person",
                target_id="p-2",
            )

    def test_lowercases_endpoint_types(self):
        edge = normalize_edge(
            tenant_id=TENANT_A,
            edge_type="champion_for",
            source_type="PERSON",
            source_id="p-1",
            target_type="Company",
            target_id="c-1",
        )
        assert edge.source_type == "person"
        assert edge.target_type == "company"

    def test_company_edges_allowed(self):
        edge = normalize_edge(
            tenant_id=TENANT_A,
            edge_type="champion_for",
            source_type="person",
            source_id="p-1",
            target_type="company",
            target_id="c-1",
        )
        assert edge.target_type == "company"

    def test_confidence_coerced_to_float_and_clamped_ok(self):
        edge = normalize_edge(
            tenant_id=TENANT_A,
            edge_type="influences",
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-2",
            confidence=0.8,
        )
        assert edge.confidence == 0.8

    def test_generated_id_and_normalized_fields_present(self):
        edge = normalize_edge(
            tenant_id=TENANT_A,
            edge_type="introduced_by",
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-2",
            basis="manual",
            evidence=[{"source": "interview", "notes": "intro at Aug summit"}],
            created_by="u-1",
        )
        assert edge.id
        assert edge.basis == "manual"
        assert edge.evidence == [{"source": "interview", "notes": "intro at Aug summit"}]
        assert edge.created_by == "u-1"
        assert edge.superseded_at is None
        assert edge.created_at

    def test_observed_at_preserved_when_provided(self):
        edge = normalize_edge(
            tenant_id=TENANT_A,
            edge_type="blocks",
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-2",
            observed_at="2026-08-01T00:00:00+00:00",
        )
        assert edge.observed_at == "2026-08-01T00:00:00+00:00"

    def test_basis_truncated_to_64_chars(self):
        edge = normalize_edge(
            tenant_id=TENANT_A,
            edge_type="influences",
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-2",
            basis="b" * 80,
        )
        assert len(edge.basis) == 64

    def test_as_dict_round_trips_shape(self):
        edge = normalize_edge(
            tenant_id=TENANT_A,
            edge_type="reports_to",
            source_type="person",
            source_id="p-1",
            target_type="person",
            target_id="p-2",
            confidence=0.9,
        )
        data = edge.as_dict()
        assert data["edge_type"] == "reports_to"
        assert data["tenant_id"] == TENANT_A
        assert data["confidence"] == 0.9
        assert data["evidence"] == []
        assert {"id", "edge_type", "source_id", "target_id", "basis", "evidence",
                "confidence", "observed_at", "superseded_at", "created_by", "created_at"} <= set(data)


class TestShapeStability:
    def test_vocabulary_sets_match_tuples(self):
        assert EDGE_TYPE_SET == set(RELATIONSHIP_EDGE_TYPES)
        assert ENDPOINT_TYPE_SET == {"person", "company"}

    def test_matrix_gap_coverage(self):
        """Row 99 (Commercial Relationship Model) asks for a typed edge model
        for reports_to, influences, champion_for, blocks, introduced_by. Each
        of those must be constructible; the model is NOT a general graph (no
        Neo4j), so coverage is exactly these five plus the endpoints."""
        assert all(etype in EDGE_TYPE_SET for etype in
                   ("reports_to", "influences", "champion_for", "blocks", "introduced_by"))