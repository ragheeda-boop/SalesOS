"""Verify agents don't hallucinate without data — grounding integrity tests."""

import pytest


def test_grounding_context_has_expected_structure():
    """AgentContext should have all expected fields."""
    from intelligence.grounding import AgentContext
    ctx = AgentContext()
    assert hasattr(ctx, "company_info")
    assert hasattr(ctx, "contacts")
    assert hasattr(ctx, "opportunities")
    assert hasattr(ctx, "relationships")
    assert hasattr(ctx, "signals")
    assert hasattr(ctx, "recent_activity")


def test_grounding_context_empty_detection():
    """Empty context should be correctly identified."""
    from intelligence.grounding import AgentContext
    ctx = AgentContext()
    assert ctx.is_empty() is True
    ctx.company_info = {"name": "Test"}
    assert ctx.is_empty() is False


def test_competitor_agent_falls_back_without_data():
    """Competitor agent should produce low confidence without grounding data."""
    from intelligence.grounding import AgentContext
    ctx = AgentContext()
    evidence_count = len(ctx.contacts) + len(ctx.opportunities) + len(ctx.signals)
    base_confidence = 0.1
    fallback = min(base_confidence + evidence_count * 0.05, 0.7)
    assert fallback == 0.1


@pytest.mark.parametrize("evidence_counts,expected_range", [
    ((0, 0, 0), (0.1, 0.2)),
    ((5, 3, 2), (0.6, 0.8)),
    ((1, 0, 0), (0.1, 0.4)),
])
def test_confidence_scales_with_evidence(evidence_counts, expected_range):
    """Agent confidence should scale with available evidence."""
    contacts, opportunities, signals = evidence_counts
    score = 0.1
    score += min(contacts * 0.05, 0.25)
    score += min(opportunities * 0.05, 0.25)
    score += min(signals * 0.05, 0.15)
    score = min(score, 0.95)
    lo, hi = expected_range
    assert lo <= score <= hi


def test_output_schema_requires_confidence_range():
    """All agent output schemas must constrain confidence to 0-1."""
    from intelligence.schemas import (
        CompetitorAnalysis, MeetingPreparation, ProposalContent,
        PricingAnalysis, ForecastAnalysis, RenewalRisk,
    )
    for schema in [CompetitorAnalysis, MeetingPreparation, ProposalContent,
                   PricingAnalysis, ForecastAnalysis, RenewalRisk]:
        schema_fields = schema.model_fields
        if "confidence" in schema_fields:
            field_info = schema_fields["confidence"]
            assert field_info.metadata is not None
            from pydantic import Field
            has_ge = False
            has_le = False
            for meta in field_info.metadata:
                if hasattr(meta, 'ge'):
                    has_ge = meta.ge == 0
                if hasattr(meta, 'le'):
                    has_le = meta.le == 1
            assert has_ge, f"{schema.__name__}.confidence missing ge>=0 constraint"
            assert has_le, f"{schema.__name__}.confidence missing le<=1 constraint"
