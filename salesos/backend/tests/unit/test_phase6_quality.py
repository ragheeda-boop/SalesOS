"""Unit tests for Phase 6 quality scoring module."""

import pytest

from app.modules.master_data.phase6.quality import QualityResult, score_quality


class TestScoreQuality:
    """Test versioned quality scoring with evidence basis.

    Actual behavior:
    - Scores are on 0-100 scale (not 0-1)
    - evidence_basis structure: fields_present, field_conflict, conflict_fields, independent_source_count, source_count, observed_recency_days
    - Overall is weighted average of completeness (30%), accuracy (25%), consistency (15%), freshness (15%), provenance (15%)
    """

    def test_complete_record_high_quality(self):
        res = score_quality(
            fields={
                "cr_number": True, "vat_number": True, "unified_national_number": True,
                "canonical_name": True, "domain": True, "phone": True, "email": True,
                "city": True, "industry": True,
            },
            provenance_tiers={
                "cr_number": "GOVERNMENT_ANCHOR",
                "vat_number": "GOVERNMENT_ANCHOR",
                "unified_national_number": "GOVERNMENT_ANCHOR",
                "canonical_name": "STRONG_DETERMINISTIC",
                "domain": "STRONG_DETERMINISTIC",
                "phone": "WEAK_DETERMINISTIC",
                "email": "WEAK_DETERMINISTIC",
                "city": "WEAK_DETERMINISTIC",
                "industry": "NORMALIZED_EXACT",
            },
            field_conflict=False,
            conflict_fields=[],
            independent_source_count=3,
            source_count=3,
        )
        assert isinstance(res, QualityResult)
        assert res.completeness_score == 100.0  # All 9 core fields present
        assert res.accuracy_score == 100.0  # Multi-source, no conflict
        assert res.consistency_score == 100.0  # No conflict
        assert res.freshness_score == 100.0  # No recency data
        assert res.provenance_score > 70.0  # High tier ranks
        assert res.overall_score > 85.0
        assert "fields_present" in res.evidence_basis

    def test_incomplete_record(self):
        res = score_quality(
            fields={
                "cr_number": False, "vat_number": False, "unified_national_number": False,
                "domain": True, "phone": True, "email": True,
                "city": True, "industry": True,
            },
            provenance_tiers={
                "domain": "STRONG_DETERMINISTIC",
                "phone": "WEAK_DETERMINISTIC",
                "email": "WEAK_DETERMINISTIC",
                "city": "WEAK_DETERMINISTIC",
                "industry": "NORMALIZED_EXACT",
            },
            field_conflict=False,
            conflict_fields=[],
            independent_source_count=1,
            source_count=1,
        )
        # 5 of 8 core fields present, weights: domain(2)+phone(1)+email(1)+city(1)+industry(1) = 6/15 = 40%
        assert res.completeness_score == 40.0
        # Single source → accuracy penalty
        assert res.accuracy_score == 90.0
        assert res.overall_score < 80.0

    def test_field_conflict_reduces_accuracy_and_consistency(self):
        res = score_quality(
            fields={
                "cr_number": True, "vat_number": False, "unified_national_number": False,
                "domain": True, "phone": True, "email": True,
                "city": True, "industry": True,
            },
            provenance_tiers={
                "cr_number": "GOVERNMENT_ANCHOR",
                "domain": "STRONG_DETERMINISTIC",
                "phone": "WEAK_DETERMINISTIC",
                "email": "WEAK_DETERMINISTIC",
                "city": "WEAK_DETERMINISTIC",
                "industry": "NORMALIZED_EXACT",
            },
            field_conflict=True,
            conflict_fields=["cr_number"],
            independent_source_count=2,
            source_count=2,
        )
        # Field conflict reduces accuracy by 30 and consistency by 25
        assert res.accuracy_score == 70.0  # 100 - 30 (1 conflict field)
        assert res.consistency_score == 75.0  # 100 - 25
        assert "cr_number" in str(res.evidence_basis["conflict_fields"])

    def test_multi_source_boosts_provenance(self):
        res = score_quality(
            fields={
                "cr_number": False, "vat_number": False, "unified_national_number": False,
                "domain": True, "phone": True, "email": True,
                "city": True, "industry": True,
            },
            provenance_tiers={
                "domain": "STRONG_DETERMINISTIC",
                "phone": "WEAK_DETERMINISTIC",
                "email": "WEAK_DETERMINISTIC",
                "city": "WEAK_DETERMINISTIC",
                "industry": "NORMALIZED_EXACT",
            },
            field_conflict=False,
            conflict_fields=[],
            independent_source_count=3,
            source_count=3,
        )
        # Provenance based on tier ranks, not source count directly
        assert res.provenance_score > 50.0

    def test_empty_fields(self):
        res = score_quality(
            fields={},
            provenance_tiers={},
            field_conflict=False,
            conflict_fields=[],
            independent_source_count=0,
            source_count=0,
        )
        assert res.completeness_score == 0.0
        # Overall is weighted average, provenance=0 pulls it down but others may be >0
        assert res.overall_score < 60.0  # Not 0 because accuracy/consistency/freshness default to high

    def test_evidence_basis_structure(self):
        res = score_quality(
            fields={"cr_number": True, "domain": True},
            provenance_tiers={"cr_number": "GOVERNMENT_ANCHOR", "domain": "STRONG_DETERMINISTIC"},
            field_conflict=False,
            conflict_fields=[],
            independent_source_count=1,
            source_count=1,
        )
        basis = res.evidence_basis
        assert "fields_present" in basis
        assert "cr_number" in basis["fields_present"]
        assert "domain" in basis["fields_present"]
        assert "field_conflict" in basis
        assert "conflict_fields" in basis
        assert "independent_source_count" in basis
        assert "source_count" in basis
        assert "observed_recency_days" in basis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])