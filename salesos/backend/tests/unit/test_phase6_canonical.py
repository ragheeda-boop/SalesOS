"""Unit tests for Phase 6 canonical authority module."""

import pytest

from app.modules.master_data.phase6.canonical import (
    CanonicalCandidate,
    select_canonical,
)


class TestSelectCanonical:
    """Test authority-based survivorship (frequency NEVER used).

    Actual CanonicalCandidate structure:
    - value: the actual field value
    - source_row_id: source identifier
    - evidence_tier: GOVERNMENT_ANCHOR, STRONG_DETERMINISTIC, etc.
    - authority_score: computed from tier
    - selection_reason: why this was selected
    - observed_at: ISO timestamp
    """

    def test_government_anchor_highest_authority(self):
        candidates = [
            CanonicalCandidate("1010101010", "src1", "GOVERNMENT_ANCHOR", 1.0, "test", "2024-01-01"),
            CanonicalCandidate("1010101011", "src2", "STRONG_DETERMINISTIC", 0.85, "test", "2024-01-02"),
            CanonicalCandidate("1010101012", "src3", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-03"),
        ]
        chosen = select_canonical(candidates)
        assert chosen.value == "1010101010"
        assert chosen.source_row_id == "src1"
        assert chosen.evidence_tier == "GOVERNMENT_ANCHOR"

    def test_strong_deterministic_over_weak(self):
        candidates = [
            CanonicalCandidate("1010101011", "src2", "STRONG_DETERMINISTIC", 0.85, "test", "2024-01-02"),
            CanonicalCandidate("1010101012", "src3", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-03"),
        ]
        chosen = select_canonical(candidates)
        assert chosen.value == "1010101011"
        assert chosen.evidence_tier == "STRONG_DETERMINISTIC"

    def test_normalized_exact_over_fuzzy(self):
        candidates = [
            CanonicalCandidate("Acme Corp", "src1", "NORMALIZED_EXACT", 0.5, "test", "2024-01-01"),
            CanonicalCandidate("Acme Corporation", "src2", "FUZZY", 0.3, "test", "2024-01-02"),
        ]
        chosen = select_canonical(candidates)
        assert chosen.value == "Acme Corp"
        assert chosen.evidence_tier == "NORMALIZED_EXACT"

    def test_frequency_never_used(self):
        """Frequency must NEVER determine canonical - only authority."""
        # Many weak sources vs one strong
        candidates = [
            CanonicalCandidate("Value A", "src1", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-01"),
            CanonicalCandidate("Value A", "src2", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-02"),
            CanonicalCandidate("Value A", "src3", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-03"),
            CanonicalCandidate("Value A", "src4", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-04"),
            CanonicalCandidate("Value B", "src5", "STRONG_DETERMINISTIC", 0.85, "test", "2024-01-05"),
        ]
        chosen = select_canonical(candidates)
        # Strong deterministic wins even though "Value A" appears 4x vs 1x
        assert chosen.value == "Value B"
        assert chosen.evidence_tier == "STRONG_DETERMINISTIC"

    def test_tiebreaker_most_recent(self):
        candidates = [
            CanonicalCandidate("Value A", "src1", "STRONG_DETERMINISTIC", 0.85, "test", "2024-01-01"),
            CanonicalCandidate("Value B", "src2", "STRONG_DETERMINISTIC", 0.85, "test", "2024-01-02"),
        ]
        chosen = select_canonical(candidates)
        # Tie on authority -> most recent observed_at wins
        assert chosen.value == "Value B"
        assert chosen.source_row_id == "src2"

    def test_is_current_flag_not_in_candidate(self):
        """CanonicalCandidate doesn't have is_current flag - it's for pipeline storage."""
        candidates = [
            CanonicalCandidate("Old Value", "src1", "STRONG_DETERMINISTIC", 0.85, "test", "2024-01-01"),
            CanonicalCandidate("New Value", "src2", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-02"),
        ]
        chosen = select_canonical(candidates)
        # Authority wins regardless of recency
        assert chosen.value == "Old Value"
        assert chosen.evidence_tier == "STRONG_DETERMINISTIC"

    def test_empty_candidates(self):
        chosen = select_canonical([])
        assert chosen is None

    def test_single_candidate(self):
        candidates = [CanonicalCandidate("Only Value", "src1", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-01")]
        chosen = select_canonical(candidates)
        assert chosen.value == "Only Value"
        assert chosen.source_row_id == "src1"

    def test_empty_value_filtered(self):
        candidates = [
            CanonicalCandidate("", "src1", "STRONG_DETERMINISTIC", 0.85, "test", "2024-01-01"),
            CanonicalCandidate("Valid Value", "src2", "WEAK_DETERMINISTIC", 0.6, "test", "2024-01-02"),
        ]
        chosen = select_canonical(candidates)
        assert chosen.value == "Valid Value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])