"""Unit tests for Phase 6 classification module (OPTION C)."""

import pytest

from app.modules.master_data.phase6.classification import (
    IdentityState,
    SalesReadiness,
    classify_corrected,
    evaluate_source_field_agreement,
    is_generic_domain,
    is_real_domain,
)


class TestIsGenericDomain:
    """Test generic domain detection (case-insensitive, substring match)."""

    @pytest.mark.parametrize("domain,expected", [
        ("gmail.com", True),
        ("GMAIL.COM", True),
        ("gmai.com", True),
        ("hotmail.com", True),
        ("hotmai.com", True),
        ("yahoo.com", True),
        ("yaho.com", True),
        ("outlook.com", True),
        ("windowslive.com", True),
        ("live.com", True),
        ("icloud.com", True),
        ("msn.com", True),
        ("yopmail.com", True),
        ("mail.com", True),
        ("me.com", True),
        ("boxomail.com", True),
        ("drmail.com", True),
        ("company.com", False),
        ("iics-sa.com", False),
        ("example.org", False),
    ])
    def test_generic_domains(self, domain, expected):
        assert is_generic_domain(domain) == expected


class TestIsRealDomain:
    """Test real domain detection (not None, not empty, not generic)."""

    @pytest.mark.parametrize("domain,expected", [
        ("company.com", True),
        ("iics-sa.com", True),
        ("gmail.com", False),
        ("", False),
        (None, False),
        ("  ", False),
    ])
    def test_real_domains(self, domain, expected):
        assert is_real_domain(domain) == expected


class TestEvaluateSourceFieldAgreement:
    """Test multi-source field agreement evaluation.

    Actual behavior: 
    - genuinely=True when ≥2 sources share ANY agreeing field (CR or domain or phone+name)
    - field_conflict=True when ≥2 sources have conflicting values on a field
    - Both can be True simultaneously (conflict on one field, agreement on another)
    """

    def test_domain_agreement_yields_genuine(self):
        genuinely, conflict, fields = evaluate_source_field_agreement(
            cr_values_by_source={"A": ["1010101010"], "B": ["2020202020"]},
            domain_values_by_source={"A": ["company.com"], "B": ["company.com"]},
        )
        # Domain agrees → genuinely=True, but CR conflicts → conflict=True
        assert genuinely is True
        assert conflict is True
        assert "cr_number" in fields

    def test_cr_conflict_detected(self):
        genuinely, conflict, fields = evaluate_source_field_agreement(
            cr_values_by_source={"A": ["1010101010"], "B": ["2020202020"]},
            domain_values_by_source={"A": ["company.com"], "B": ["other.com"]},
        )
        # Both CR and domain conflict
        assert genuinely is False
        assert conflict is True
        assert "cr_number" in fields
        assert "domain" in fields

    def test_single_source_no_conflict(self):
        genuinely, conflict, fields = evaluate_source_field_agreement(
            cr_values_by_source={"A": ["1010101010"]},
            domain_values_by_source={"A": ["company.com"]},
        )
        assert genuinely is False  # Need ≥2 sources
        assert conflict is False
        assert fields == []

    def test_empty_values_ignored(self):
        genuinely, conflict, fields = evaluate_source_field_agreement(
            cr_values_by_source={"A": ["1010101010"], "B": []},
            domain_values_by_source={"A": ["company.com"], "B": [""]},
        )
        assert genuinely is False  # B has no values
        assert conflict is False


class TestClassifyCorrected:
    """Test OPTION C classification with corrected bucket priority."""

    def test_conflicting_cr_p0(self):
        res = classify_corrected(
            cr_number="1010101010; 2020202020",
            domain="company.com",
        )
        assert res.identity_state == IdentityState.CONFLICTING_IDENTITY
        assert res.review_priority == "P0"
        assert res.sales_readiness == SalesReadiness.IDENTITY_REVIEW_REQUIRED

    def test_no_identity_signal_p4(self):
        res = classify_corrected(
            cr_number=None,
            domain="gmail.com",  # generic = not real
            apollo_account_id=None,
            has_contactable_email=True,
            has_phone=True,
        )
        assert res.identity_state == IdentityState.NO_VERIFIABLE_IDENTITY
        assert res.review_priority == "P4"
        assert res.sales_readiness == SalesReadiness.INSUFFICIENT_DATA

    def test_government_anchored_cr_matched(self):
        res = classify_corrected(
            cr_number="1010101010",
            domain="company.com",
            confidence="MATCHED",
        )
        assert res.identity_state == IdentityState.GOVERNMENT_ANCHORED
        assert res.review_priority == "P1"
        assert res.sales_readiness == SalesReadiness.SALES_READY
        assert res.has_cr is True

    def test_valid_cr_not_matched_goes_single_source(self):
        res = classify_corrected(
            cr_number="1010101010",
            domain="company.com",
            confidence="UNMATCHED",
        )
        assert res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE
        assert res.review_priority == "P2"

    def test_multi_source_domain_agreement_strong(self):
        """Genuine domain agreement across ≥2 independent sources, MATCHED conf."""
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            apollo_account_id="apollo123",
            confidence="MATCHED",
            independent_source_count=2,
            source_count=2,
            cr_values_by_source={"A": ["1010101010"], "B": ["1010101010"]},
            domain_values_by_source={"A": ["company.com"], "B": ["company.com"]},
            has_contactable_email=True,
        )
        # Domain agrees → genuinely=True, no field conflict → STRONG_MULTI_SOURCE
        assert res.identity_state == IdentityState.STRONG_MULTI_SOURCE
        assert res.review_priority == "P1"
        assert res.sales_readiness == SalesReadiness.SALES_READY

    def test_multi_source_likely_match_is_strong_multisource(self):
        """LIKELY MATCH confidence + genuine 2-source domain agreement."""
        res = classify_corrected(
            cr_number=None,
            domain="example.com",
            apollo_account_id=None,
            confidence="LIKELY MATCH",
            independent_source_count=2,
            source_count=2,
            domain_values_by_source={"A": ["example.com"], "B": ["example.com"]},
        )
        assert res.identity_state == IdentityState.STRONG_MULTI_SOURCE
        assert res.review_priority == "P1"

    def test_same_source_duplication_does_not_qualify(self):
        """Two records from the SAME source are NOT independent corroboration."""
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            apollo_account_id=None,
            confidence="MATCHED",
            independent_source_count=1,
            source_count=2,
            cr_values_by_source={"SFDA": ["1010101010", "1010101010"]},
            domain_values_by_source={"SFDA": ["company.com"]},
        )
        # Same source (single key) → len(present) < 2 → NOT genuinely corroborated.
        assert res.identity_state != IdentityState.STRONG_MULTI_SOURCE

    def test_conflicting_values_do_not_qualify(self):
        """Two independent sources with a CONFLICTING CR → not corroboration."""
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            apollo_account_id=None,
            confidence="MATCHED",
            independent_source_count=2,
            source_count=2,
            cr_values_by_source={"A": ["1010101010"], "B": ["2020202020"]},
            domain_values_by_source={"A": ["company.com"], "B": ["company.com"]},
        )
        # CR conflict → field_conflict=True → REVIEW_REQUIRED, never STRONG_MULTI_SOURCE.
        assert res.identity_state == IdentityState.REVIEW_REQUIRED
        assert res.review_priority == "P1"

    def test_unmatched_confidence_multisource_not_strong(self):
        """DI rule: STRONG_MULTI_SOURCE requires conf in (MATCHED, LIKELY MATCH)."""
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            apollo_account_id="apollo123",
            confidence="UNMATCHED",
            independent_source_count=2,
            source_count=2,
            cr_values_by_source={"A": ["1010101010"], "B": ["1010101010"]},
            domain_values_by_source={"A": ["company.com"], "B": ["company.com"]},
        )
        # UNMATCHED confidence + 2 sources + real domain, but not corroborated
        # per spec → not STRONG_MULTI_SOURCE.
        assert res.identity_state != IdentityState.STRONG_MULTI_SOURCE

    def test_multi_source_with_field_conflict_review_required(self):
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            apollo_account_id="apollo123",
            confidence="MATCHED",
            independent_source_count=2,
            source_count=2,
            cr_values_by_source={"A": ["1010101010"], "B": ["2020202020"]},
            domain_values_by_source={"A": ["company.com"], "B": ["company.com"]},
        )
        # CR conflicts → field_conflict=True → REVIEW_REQUIRED
        assert res.identity_state == IdentityState.REVIEW_REQUIRED
        assert res.review_priority == "P1"

    def test_deterministic_single_source_real_domain(self):
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            confidence="UNMATCHED",
            independent_source_count=1,
            source_count=1,
        )
        assert res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE
        assert res.review_priority == "P2"
        assert res.sales_readiness == SalesReadiness.ENRICHMENT_REQUIRED

    def test_deterministic_single_source_apollo(self):
        res = classify_corrected(
            cr_number=None,
            domain="gmail.com",  # generic, not real
            apollo_account_id="apollo123",
            confidence="UNMATCHED",
            independent_source_count=1,
            source_count=1,
        )
        assert res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE
        assert res.review_priority == "P2"

    def test_fuzzy_candidate_p3(self):
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            confidence="REVIEW REQUIRED",
            fuzzy_candidate=True,
        )
        assert res.identity_state == IdentityState.REVIEW_REQUIRED
        assert res.review_priority == "P3"

    def test_review_confidence_single_source(self):
        """Single source with REVIEW REQUIRED confidence → DETERMINISTIC_SINGLE_SOURCE."""
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            confidence="REVIEW REQUIRED",
            fuzzy_candidate=False,
        )
        # Single source + real domain → DETERMINISTIC_SINGLE_SOURCE even with REVIEW confidence
        assert res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE
        assert res.review_priority == "P2"

    def test_weak_identity_contactability_only_generic_domain(self):
        """Generic domain + contactability = NO_VERIFIABLE_IDENTITY (not WEAK_IDENTITY)."""
        res = classify_corrected(
            cr_number=None,
            domain="gmail.com",
            apollo_account_id=None,
            has_contactable_email=True,
            has_phone=False,
        )
        assert res.identity_state == IdentityState.NO_VERIFIABLE_IDENTITY
        assert res.review_priority == "P4"

    def test_generic_domain_filtered_from_identity(self):
        """OPTION C: email/phone = contactability, NOT identity."""
        res = classify_corrected(
            cr_number=None,
            domain="gmail.com",  # generic
            apollo_account_id=None,
            has_contactable_email=True,
            has_phone=True,
        )
        # No identity signal (no CR, no Apollo, no real domain)
        assert res.identity_state == IdentityState.NO_VERIFIABLE_IDENTITY
        assert res.sales_readiness == SalesReadiness.INSUFFICIENT_DATA


class TestIdentitySignals:
    """Test the corrected identity signal set: CR OR Apollo OR real-domain."""

    def test_apollo_is_identity_signal(self):
        res = classify_corrected(
            cr_number=None,
            domain="gmail.com",
            apollo_account_id="apollo123",
            has_contactable_email=False,
            has_phone=False,
        )
        assert res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE

    def test_real_domain_is_identity_signal(self):
        res = classify_corrected(
            cr_number=None,
            domain="company.com",
            apollo_account_id=None,
            has_contactable_email=False,
            has_phone=False,
        )
        assert res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE

    def test_cr_is_identity_signal(self):
        res = classify_corrected(
            cr_number="1010101010",
            domain="gmail.com",
            apollo_account_id=None,
            has_contactable_email=False,
            has_phone=False,
        )
        assert res.identity_state == IdentityState.DETERMINISTIC_SINGLE_SOURCE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])