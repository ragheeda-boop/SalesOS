"""Unit tests: CR normalization safety (P0 defect) + deterministic identity/sales classification.

Gap A (Data-Intelligence CR normalization defect): a short/multi-value raw CR must never be
concatenated into a plausible-looking government anchor. These tests lock the invariant:
  FUZZY_ONLY = NEVER_AUTO_MERGE   and   suspicious CR != trusted anchor.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from app.modules.entity_resolution.resolution_policy import (
    normalize_cr,
    classify_cr,
    assess_identity,
    IdentityState,
    SalesReadiness,
)


# ═══════════════════════════════════════════════════════════════════════════════
# GAP A: CR NORMALIZATION SAFETY
# ═══════════════════════════════════════════════════════════════════════════════

class TestNormalizeCrSafety:
    """The Data-Intelligence CR defect: multi-value / suspicious CRs are NOT concatenated."""

    def test_single_valid_cr_preserved(self):
        assert normalize_cr("1010123456") == "1010123456"
        assert normalize_cr("7001234567") == "7001234567"

    @pytest.mark.parametrize("raw", [
        "1005; 7066",       # two short tokens — must NOT concatenate to '10057066'
        "310; 4263",        # two short tokens
        "601; 5330",        # two short tokens
        "1338; 3449",       # both would concat to 8-digit false CR
        "4003; 30",         # mixed short lengths
        "4708; 5533",
        "262; 843",
        "2193; 4425",
        "2286; 1200727500", # one valid + one short sibling → ambiguous field
    ])
    def test_no_concatenation_of_multi_value(self, raw):
        # The defect previously produced a plausible 5-10 digit CR by concatenation.
        assert normalize_cr(raw) is None

    def test_rtl_control_chars_stripped(self):
        # "\u202d...\u202c" embeds a real CR inside RTL isolates — must still resolve.
        assert normalize_cr("\u202d7054210393\u202c") == "7054210393"

    def test_short_value_returns_none(self):
        assert normalize_cr("1234") is None
        assert normalize_cr("2286") is None  # 4-digit sibling of a CR list

    def test_leading_zeros_still_validated(self):
        assert normalize_cr("0001012345") == "1012345"
        assert normalize_cr("00000") is None

    def test_non_cr_noise_rejected(self):
        assert normalize_cr("ABCDE1234") is None
        assert normalize_cr("") is None
        assert normalize_cr(None) is None
        assert normalize_cr("None") is None


class TestClassifyCr:
    """classify_cr must flag suspicious/short/multi CRs so they are NOT trusted anchors."""

    def test_safe_single_anchor(self):
        assert classify_cr("7001234567") == "SAFE"

    def test_suspicious_short(self):
        assert classify_cr("1234") == "SUSPICIOUS_SHORT"
        assert classify_cr("2286") == "SUSPICIOUS_SHORT"

    def test_suspicious_multi(self):
        assert classify_cr("1005; 7066") == "SUSPICIOUS_MULTI"
        assert classify_cr("2286; 1200727500") == "SUSPICIOUS_MULTI"
        assert classify_cr("310; 4263") == "SUSPICIOUS_MULTI"

    def test_ambiguous(self):
        assert classify_cr("None") == "AMBIGUOUS"
        assert classify_cr("") == "AMBIGUOUS"
        assert classify_cr("ABCDE") == "AMBIGUOUS"
        assert classify_cr(None) == "AMBIGUOUS"


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY & SALES READINESS (Gaps B/E/F)
# ═══════════════════════════════════════════════════════════════════════════════

class TestIdentityAssessment:
    """Deterministic identity/sales classification with no fabrication and no auto-merge."""

    def test_safe_cr_is_government_anchored(self):
        a = assess_identity(cr_number="7001234567")
        assert a.identity_state == IdentityState.GOVERNMENT_ANCHORED
        assert a.sales_readiness in (SalesReadiness.SALES_READY, SalesReadiness.SALES_READY_WITH_REVIEW)

    def test_conflicting_identity_is_p0_veto(self):
        a = assess_identity(cr_number="7001234567", conflicting_identity=True)
        assert a.identity_state == IdentityState.CONFLICTING_IDENTITY
        assert a.sales_readiness == SalesReadiness.IDENTITY_REVIEW_REQUIRED
        assert a.review_priority == "P0"
        assert a.conflicts is True

    def test_suspicious_cr_is_not_anchor(self):
        """A suspicious/short CR must NOT become a government-anchored record."""
        a = assess_identity(cr_number="1234")
        assert a.identity_state != IdentityState.GOVERNMENT_ANCHORED
        assert a.sales_readiness == SalesReadiness.IDENTITY_REVIEW_REQUIRED
        assert a.has_cr is False

    def test_suspicious_multi_cr_is_not_anchor(self):
        a = assess_identity(cr_number="1005; 7066")
        assert a.identity_state != IdentityState.GOVERNMENT_ANCHORED
        assert a.sales_readiness == SalesReadiness.IDENTITY_REVIEW_REQUIRED

    def test_multi_source_strong_is_sales_ready_with_review(self):
        a = assess_identity(
            domain="acme.com", source_count=3, independent_source_count=3,
            has_contactable_email=True,
        )
        assert a.identity_state == IdentityState.STRONG_MULTI_SOURCE

    def test_fuzzy_only_never_auto_merge(self):
        a = assess_identity(fuzzy_candidate=True)
        # fuzzy-only → review/insufficient, never a trusted anchor
        assert a.identity_state in (IdentityState.REVIEW_REQUIRED, IdentityState.WEAK_IDENTITY,
                                    IdentityState.NO_VERIFIABLE_IDENTITY)

    def test_no_verifiable_identity(self):
        a = assess_identity()
        assert a.identity_state == IdentityState.NO_VERIFIABLE_IDENTITY
        assert a.sales_readiness == SalesReadiness.INSUFFICIENT_DATA
        assert a.review_priority == "P4"

    def test_weak_identity_email_only_is_not_anchor(self):
        a = assess_identity(has_contactable_email=True, has_phone=True)
        # Email/phone are contactability, NOT government identity → weak, not anchored.
        assert a.identity_state == IdentityState.WEAK_IDENTITY
        assert a.sales_readiness == SalesReadiness.ENRICHMENT_REQUIRED

    def test_free_mail_domain_is_not_strong(self):
        a = assess_identity(domain="gmail.com", has_contactable_email=True)
        assert a.identity_state == IdentityState.WEAK_IDENTITY
        assert a.identity_state != IdentityState.STRONG_MULTI_SOURCE
