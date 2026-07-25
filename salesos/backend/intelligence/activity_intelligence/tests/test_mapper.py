"""Tests for Mapper — Stage 5 of Mapping Pipeline (ADR-012 §6)."""

import pytest
from intelligence.activity_intelligence.contracts.models import (
    CandidateMatch,
    MappingResult,
    ScoredCandidate,
)
from intelligence.activity_intelligence.mapping.mapper import MappingPersister


class TestMappingPersister:
    def setup_method(self):
        self.mapper = MappingPersister()

    def test_persist_email_mapping_company(self):
        candidate = CandidateMatch(
            entity_id="comp-1",
            entity_type="company",
            method="domain_match",
            confidence=0.85,
            reason="Matched via domain",
        )
        scored = ScoredCandidate(
            candidate=candidate,
            score=0.85,
            reason="Matched via domain",
        )

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            self.mapper.persist_email_mapping("msg-1", scored)
        )

        assert result.mapped is True
        assert result.source_id == "msg-1"
        assert result.company_id == "comp-1"
        assert result.confidence == 0.85
        assert result.method == "domain_match"

    def test_persist_email_mapping_opportunity(self):
        candidate = CandidateMatch(
            entity_id="OPP-123",
            entity_type="opportunity",
            method="explicit_ref",
            confidence=1.0,
        )
        scored = ScoredCandidate(
            candidate=candidate,
            score=1.0,
            reason="Explicit reference",
        )

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            self.mapper.persist_email_mapping("msg-2", scored)
        )

        assert result.mapped is True
        assert result.opportunity_id == "OPP-123"
        assert result.entity_type == "opportunity"

    def test_build_unresolved(self):
        result = self.mapper.build_unresolved("msg-1", "no_match")
        assert not result.mapped
        assert result.source_id == "msg-1"
        assert result.reason == "no_match"

    def test_build_unresolved_default_reason(self):
        result = self.mapper.build_unresolved("msg-2")
        assert not result.mapped
        assert result.reason == "no_candidate_above_threshold"

    def test_mapping_provenance(self):
        candidate = CandidateMatch(
            entity_id="comp-1",
            entity_type="company",
            method="ai_match",
            confidence=0.55,
        )
        scored = ScoredCandidate(
            candidate=candidate,
            score=0.55,
            reason="AI match",
        )

        provenance = {"model": "gpt-4", "input_tokens": 150}

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            self.mapper.persist_email_mapping(
                "msg-3", scored, mapping_provenance=provenance
            )
        )

        assert result.mapped is True
        assert result.method == "ai_match"
