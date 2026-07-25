"""Tests for Confidence Scorer (ADR-012 §6)."""

import pytest
from intelligence.activity_intelligence.contracts.models import CandidateMatch, ScoredCandidate
from intelligence.activity_intelligence.mapping.confidence import (
    ConfidenceScorer,
    METHOD_WEIGHTS,
)


class TestConfidenceScorer:
    def setup_method(self):
        self.scorer = ConfidenceScorer(threshold=0.5)

    def test_method_weights_defined(self):
        assert METHOD_WEIGHTS["explicit_ref"] == 1.0
        assert METHOD_WEIGHTS["opportunity_lookup"] == 0.9
        assert METHOD_WEIGHTS["contact_lookup"] == 0.8
        assert METHOD_WEIGHTS["domain_match"] == 0.6
        assert METHOD_WEIGHTS["ai_match"] == 0.4

    def test_score_single_candidate_above_threshold(self):
        candidate = CandidateMatch(
            entity_id="comp-1",
            entity_type="company",
            method="domain_match",
            confidence=0.6,
            reason="Matched via domain",
        )
        result = self.scorer.score([candidate])
        assert result is not None
        assert result.score == 0.6
        assert result.candidate.entity_id == "comp-1"

    def test_score_single_candidate_below_threshold(self):
        candidate = CandidateMatch(
            entity_id="comp-1",
            entity_type="company",
            method="ai_match",
            confidence=0.3,
        )
        result = self.scorer.score([candidate])
        assert result is None

    def test_score_multiple_candidates_returns_best(self):
        candidates = [
            CandidateMatch(entity_id="comp-1", entity_type="company", method="ai_match", confidence=0.4),
            CandidateMatch(entity_id="comp-2", entity_type="company", method="domain_match", confidence=0.6),
            CandidateMatch(entity_id="comp-3", entity_type="company", method="explicit_ref", confidence=1.0),
        ]
        result = self.scorer.score(candidates)
        assert result is not None
        assert result.candidate.method == "explicit_ref"
        assert result.score == 1.0

    def test_score_all_returns_sorted(self):
        candidates = [
            CandidateMatch(entity_id="comp-1", entity_type="company", method="ai_match", confidence=0.4),
            CandidateMatch(entity_id="comp-2", entity_type="company", method="domain_match", confidence=0.6),
            CandidateMatch(entity_id="comp-3", entity_type="company", method="explicit_ref", confidence=1.0),
        ]
        results = self.scorer.score_all(candidates)
        assert len(results) == 2  # ai_match below 0.5 threshold filtered out
        assert results[0].score == 1.0  # Best first
        assert results[1].score == 0.6

    def test_score_empty_candidates(self):
        result = self.scorer.score([])
        assert result is None

    def test_custom_threshold(self):
        scorer = ConfidenceScorer(threshold=0.8)
        candidate = CandidateMatch(
            entity_id="comp-1",
            entity_type="company",
            method="domain_match",
            confidence=0.6,
        )
        result = scorer.score([candidate])
        assert result is None  # Below 0.8 threshold

    def test_score_uses_candidate_confidence(self):
        candidate = CandidateMatch(
            entity_id="comp-1",
            entity_type="company",
            method="ai_match",
            confidence=0.55,  # Overrides default ai_match weight of 0.4
        )
        result = self.scorer.score([candidate])
        assert result is not None
        assert result.score == 0.55
