"""Unit tests for Phase 6 sales readiness module."""

import pytest

from app.modules.master_data.phase6.readiness import (
    ReadinessResult,
    SalesReadiness,
    recompute_sales_readiness,
)
from app.modules.master_data.phase6.classification import IdentityState


class TestRecomputeSalesReadiness:
    """Test versioned sales readiness recalculation.

    Actual behavior per readiness.py:
    - CONFLICTING_IDENTITY → IDENTITY_REVIEW_REQUIRED
    - NO_VERIFIABLE_IDENTITY → INSUFFICIENT_DATA
    - GOVERNMENT_ANCHORED / STRONG_MULTI_SOURCE + channel → SALES_READY
    - GOVERNMENT_ANCHORED / STRONG_MULTI_SOURCE + no channel → ENRICHMENT_REQUIRED
    - DETERMINISTIC_SINGLE_SOURCE + channel/domain → SALES_READY_WITH_REVIEW (if channel) or ENRICHMENT_REQUIRED
    - REVIEW_REQUIRED → ENRICHMENT_REQUIRED
    - WEAK_IDENTITY → ENRICHMENT_REQUIRED
    """

    def test_government_anchored_ready_with_channel(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.GOVERNMENT_ANCHORED,
            has_contactable_email=True,
            has_phone=True,
            has_real_domain=True,
        )
        assert res.sales_readiness == SalesReadiness.SALES_READY
        assert "GOVERNMENT_ANCHORED" in str(res.basis)

    def test_government_anchored_enrichment_no_channel(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.GOVERNMENT_ANCHORED,
            has_contactable_email=False,
            has_phone=False,
            has_real_domain=True,
        )
        assert res.sales_readiness == SalesReadiness.ENRICHMENT_REQUIRED

    def test_strong_multi_source_ready(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.STRONG_MULTI_SOURCE,
            has_contactable_email=True,
            has_phone=True,
            has_real_domain=True,
        )
        assert res.sales_readiness == SalesReadiness.SALES_READY

    def test_deterministic_single_source_with_channel(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.DETERMINISTIC_SINGLE_SOURCE,
            has_contactable_email=True,
            has_phone=True,
            has_real_domain=True,
        )
        assert res.sales_readiness == SalesReadiness.SALES_READY_WITH_REVIEW

    def test_deterministic_single_source_domain_only(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.DETERMINISTIC_SINGLE_SOURCE,
            has_contactable_email=False,
            has_phone=False,
            has_real_domain=True,
        )
        assert res.sales_readiness == SalesReadiness.ENRICHMENT_REQUIRED

    def test_review_required_enrichment(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.REVIEW_REQUIRED,
            has_contactable_email=True,
            has_phone=True,
            has_real_domain=True,
        )
        assert res.sales_readiness == SalesReadiness.ENRICHMENT_REQUIRED

    def test_conflicting_identity_review(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.CONFLICTING_IDENTITY,
            has_contactable_email=True,
            has_phone=True,
            has_real_domain=True,
        )
        assert res.sales_readiness == SalesReadiness.IDENTITY_REVIEW_REQUIRED

    def test_no_verifiable_identity_insufficient(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.NO_VERIFIABLE_IDENTITY,
            has_contactable_email=False,
            has_phone=False,
            has_real_domain=False,
        )
        assert res.sales_readiness == SalesReadiness.INSUFFICIENT_DATA

    def test_weak_identity_enrichment(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.WEAK_IDENTITY,
            has_contactable_email=True,
            has_phone=True,
            has_real_domain=False,
        )
        assert res.sales_readiness == SalesReadiness.ENRICHMENT_REQUIRED

    def test_weak_identity_no_channel_enrichment(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.WEAK_IDENTITY,
            has_contactable_email=False,
            has_phone=False,
            has_real_domain=False,
        )
        assert res.sales_readiness == SalesReadiness.ENRICHMENT_REQUIRED

    def test_basis_structure(self):
        res = recompute_sales_readiness(
            identity_state=IdentityState.GOVERNMENT_ANCHORED,
            has_contactable_email=True,
            has_phone=True,
            has_real_domain=True,
        )
        basis = res.basis
        assert "identity_state" in basis
        assert "has_contactable_email" in basis
        assert "has_phone" in basis
        assert "has_real_domain" in basis
        assert basis["identity_state"] == "GOVERNMENT_ANCHORED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])