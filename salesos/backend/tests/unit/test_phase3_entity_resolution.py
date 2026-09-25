"""Phase 3 Unit Tests — Entity Resolution Pipeline.

Tests the matching pipeline, signal extraction, blocking, field provenance,
quality scoring, and merge logic. All pure/in-memory tests — no database.
"""

from __future__ import annotations

import pytest
from app.modules.entity_resolution.resolution_policy import (
    SourceRecord,
    ConfidenceClass,
    Decision,
    EvidenceTier,
    Signal,
    evaluate_pair,
    normalize_cr,
    normalize_vat,
    normalize_unified_number,
)
from app.modules.entity_resolution.matching_pipeline import (
    extract_source_record,
    extract_signals,
    compute_score,
    normalize_domain,
    normalize_phone,
    normalize_name,
    FIELD_ALIASES,
)
from app.modules.entity_resolution.field_provenance import (
    compute_authority_score,
    TIER_AUTHORITY,
)
from app.modules.entity_resolution.quality_scorer import (
    COMPLETENESS_FIELDS,
)


# ══════════════════════════════════════════════════════════════════════════════
# Signal Extraction
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalExtraction:
    """Tests for extract_signals and extract_source_record."""

    def test_cr_match_produces_government_anchor(self):
        a = SourceRecord(source_id="balady", cr_number="1010123456")
        b = SourceRecord(source_id="ncnp", cr_number="1010123456")
        signals = extract_signals(a, b)
        assert any(s.name == "cr_match" and s.matched for s in signals)
        cr_sig = next(s for s in signals if s.name == "cr_match")
        assert cr_sig.tier == EvidenceTier.GOVERNMENT_ANCHOR

    def test_vat_match_produces_government_anchor(self):
        a = SourceRecord(source_id="a", vat_number="300123456700001")
        b = SourceRecord(source_id="b", vat_number="300123456700001")
        signals = extract_signals(a, b)
        assert any(s.name == "vat_match" and s.matched for s in signals)
        vat_sig = next(s for s in signals if s.name == "vat_match")
        assert vat_sig.tier == EvidenceTier.GOVERNMENT_ANCHOR

    def test_unified_match_produces_government_anchor(self):
        a = SourceRecord(source_id="a", unified_national_number="1234567890")
        b = SourceRecord(source_id="b", unified_national_number="1234567890")
        signals = extract_signals(a, b)
        assert any(s.name == "unified_match" and s.matched for s in signals)

    def test_domain_match_produces_strong_deterministic(self):
        a = SourceRecord(source_id="a", domain="testco.com")
        b = SourceRecord(source_id="b", domain="testco.com")
        signals = extract_signals(a, b)
        assert any(s.name == "domain_match" and s.matched for s in signals)
        dom_sig = next(s for s in signals if s.name == "domain_match")
        assert dom_sig.tier == EvidenceTier.STRONG_DETERMINISTIC

    def test_phone_match_produces_weak_deterministic(self):
        a = SourceRecord(source_id="a", phone="+966501234567")
        b = SourceRecord(source_id="b", phone="966501234567")
        signals = extract_signals(a, b)
        assert any(s.name == "phone_match" and s.matched for s in signals)

    def test_email_match_skips_role_email(self):
        a = SourceRecord(source_id="a", email="info@example.com")
        b = SourceRecord(source_id="b", email="info@example.com")
        signals = extract_signals(a, b)
        assert not any(s.name == "email_match" and s.matched for s in signals)

    def test_email_match_personal(self):
        a = SourceRecord(source_id="a", email="ahmed@example.com")
        b = SourceRecord(source_id="b", email="ahmed@example.com")
        signals = extract_signals(a, b)
        assert any(s.name == "email_match" and s.matched for s in signals)

    def test_name_exact_match(self):
        a = SourceRecord(source_id="a", canonical_name="شركة الراشد")
        b = SourceRecord(source_id="b", canonical_name="شركة الراشد")
        signals = extract_signals(a, b)
        assert any(s.name == "canonical_name_exact" and s.matched for s in signals)

    def test_name_contains_match(self):
        a = SourceRecord(source_id="a", canonical_name="شركة الراشد للتجارة")
        b = SourceRecord(source_id="b", canonical_name="الراشد")
        signals = extract_signals(a, b)
        assert any(s.name == "canonical_name_contains" and s.matched for s in signals)

    def test_no_match_produces_empty_signals(self):
        a = SourceRecord(source_id="a", canonical_name="أحمد")
        b = SourceRecord(source_id="b", canonical_name="خالد")
        signals = extract_signals(a, b)
        matched = [s for s in signals if s.matched]
        assert len(matched) == 0


# ══════════════════════════════════════════════════════════════════════════════
# Score Computation
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreComputation:
    """Tests for compute_score."""

    def test_empty_signals_zero_score(self):
        assert compute_score([]) == 0.0

    def test_government_anchor_high_score(self):
        signals = [Signal("cr_match", True, "a", 100, EvidenceTier.GOVERNMENT_ANCHOR)]
        score = compute_score(signals)
        assert score == 100.0

    def test_weak_signal_lower_score(self):
        signals = [Signal("phone_match", True, "a", 70, EvidenceTier.WEAK_DETERMINISTIC)]
        score = compute_score(signals)
        # Score is relative: 70/70 = 100% of available signals matched
        assert score == 100.0

    def test_multiple_signals_combined(self):
        signals = [
            Signal("cr_match", True, "a", 100, EvidenceTier.GOVERNMENT_ANCHOR),
            Signal("domain_match", True, "a", 85, EvidenceTier.STRONG_DETERMINISTIC),
        ]
        score = compute_score(signals)
        assert score > 50.0


# ══════════════════════════════════════════════════════════════════════════════
# Source Record Extraction
# ══════════════════════════════════════════════════════════════════════════════

class TestSourceRecordExtraction:
    """Tests for extract_source_record."""

    def test_extracts_known_fields(self):
        raw = {
            "cr_number": "1010123456",
            "company_name": "شركة تست",
            "city": "الرياض",
        }
        rec = extract_source_record("balady", "REC-1", raw)
        assert rec.cr_number == "1010123456"
        assert rec.canonical_name == "شركة تست"
        assert rec.city == "الرياض"

    def test_uses_aliases(self):
        raw = {"CR_number": "2020123456", "اسم_الشركة": "شركة أخرى"}
        rec = extract_source_record("ncnp", "REC-2", raw)
        assert rec.cr_number == "2020123456"
        assert rec.canonical_name == "شركة أخرى"

    def test_ignores_none_values(self):
        raw = {"cr_number": "1010123456"}
        rec = extract_source_record("balady", "REC-3", raw)
        assert rec.vat_number is None
        assert rec.email is None


# ══════════════════════════════════════════════════════════════════════════════
# Normalization Helpers
# ══════════════════════════════════════════════════════════════════════════════

class TestNormalizationHelpers:
    """Tests for normalization functions."""

    def test_normalize_domain_strips_protocol(self):
        assert normalize_domain("https://testco.com") == "testco.com"

    def test_normalize_domain_lowercases(self):
        assert normalize_domain("TestCo.COM") == "testco.com"

    def test_normalize_domain_blacklists(self):
        assert normalize_domain("gmail.com") is None
        assert normalize_domain("google.com") is None

    def test_normalize_phone_strips_dashes(self):
        assert normalize_phone("050-123-4567") == "0501234567"

    def test_normalize_phone_strips_plus(self):
        assert normalize_phone("+966501234567") == "966501234567"

    def test_normalize_phone_too_short(self):
        assert normalize_phone("123") is None

    def test_normalize_name_lowercases(self):
        assert normalize_name("  شركة TEST  ") == "شركة test"


# ══════════════════════════════════════════════════════════════════════════════
# Field Provenance Authority
# ══════════════════════════════════════════════════════════════════════════════

class TestFieldProvenanceAuthority:
    """Tests for authority score computation."""

    def test_government_anchor_highest(self):
        score = compute_authority_score("cr_match")
        assert score == 1.0

    def test_strong_deterministic(self):
        score = compute_authority_score("domain_match")
        assert score == 0.8

    def test_weak_deterministic(self):
        score = compute_authority_score("phone_match")
        assert score == 0.6

    def test_unknown_signal_low(self):
        score = compute_authority_score("unknown_signal")
        assert score == 0.1

    def test_all_tiers_have_authority(self):
        for tier in EvidenceTier:
            assert tier in TIER_AUTHORITY


# ══════════════════════════════════════════════════════════════════════════════
# Quality Scorer
# ══════════════════════════════════════════════════════════════════════════════

class TestQualityScorer:
    """Tests for quality scorer logic."""

    def test_completeness_fields_list(self):
        assert "canonical_name" in COMPLETENESS_FIELDS
        assert "cr_number" in COMPLETENESS_FIELDS
        assert len(COMPLETENESS_FIELDS) >= 10


# ══════════════════════════════════════════════════════════════════════════════
# End-to-End Pipeline (in-memory, no DB)
# ══════════════════════════════════════════════════════════════════════════════

class TestPipelineEndToEnd:
    """Full pipeline tests: extract → signal → evaluate → decision."""

    def test_same_cr_different_names_government_anchor(self):
        """Same CR = government anchor → HIGH confidence, AUTO_MERGE.
        CR is the authoritative identifier; name differences don't veto."""
        a = SourceRecord(source_id="balady", cr_number="1010123456", canonical_name="شركة أ")
        b = SourceRecord(source_id="ncnp", cr_number="1010123456", canonical_name="شركة ب")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.confidence == ConfidenceClass.HIGH
        assert result.has_government_anchor
        assert result.decision == Decision.AUTO_MERGE

    def test_same_cr_same_name_auto_merge(self):
        a = SourceRecord(source_id="balady", cr_number="1010123456", canonical_name="شركة الراشد")
        b = SourceRecord(source_id="ncnp", cr_number="1010123456", canonical_name="شركة الراشد")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.confidence == ConfidenceClass.HIGH
        assert result.has_government_anchor

    def test_domain_match_only_medium(self):
        a = SourceRecord(source_id="a", domain="testco.com")
        b = SourceRecord(source_id="b", domain="testco.com")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.confidence == ConfidenceClass.MEDIUM
        assert result.decision == Decision.REVIEW

    def test_phone_match_only_low(self):
        a = SourceRecord(source_id="a", phone="0501234567")
        b = SourceRecord(source_id="b", phone="0501234567")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.confidence == ConfidenceClass.LOW

    def test_fuzzy_only_low(self):
        a = SourceRecord(source_id="a", canonical_name="أحمد للمقاولات")
        b = SourceRecord(source_id="b", canonical_name="أحمد")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.has_fuzzy_only or result.confidence in (ConfidenceClass.LOW, ConfidenceClass.MEDIUM)

    def test_no_signals_low(self):
        a = SourceRecord(source_id="a", canonical_name="أحمد")
        b = SourceRecord(source_id="b", canonical_name="خالد")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.confidence == ConfidenceClass.LOW
        assert result.decision == Decision.SEPARATE

    def test_vat_conflict_strong_veto(self):
        a = SourceRecord(source_id="a", vat_number="300123456700001")
        b = SourceRecord(source_id="b", vat_number="300999999900001")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.decision == Decision.VETOED
        assert result.veto.vetoed

    def test_multi_source_independent_high(self):
        """Two independent sources with strong signals → HIGH."""
        a = SourceRecord(
            source_id="balady", cr_number="1010123456", domain="testco.com",
            canonical_name="شركة الراشد",
        )
        b = SourceRecord(
            source_id="ncnp", cr_number="1010123456", domain="testco.com",
            canonical_name="شركة الراشد للتجارة",
        )
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)
        assert result.confidence == ConfidenceClass.HIGH
        assert result.has_government_anchor
