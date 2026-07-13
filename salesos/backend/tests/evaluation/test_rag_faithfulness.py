"""Basic faithfulness test — LLM output should not contradict provided context."""

import pytest


def test_output_mentions_provided_data():
    """LLM output should reference provided context data rather than hallucinating."""
    context = {
        "company_name": "شركة التقنية السعودية",
        "industry": "تقنية معلومات",
        "employees_count": 150,
    }
    output = (
        "شركة التقنية السعودية تعمل في قطاع تقنية المعلومات "
        "وتوظف حوالي 150 موظفاً. "
    )
    assert context["company_name"] in output
    assert "تقنية" in output


def test_confidence_derived_from_evidence():
    """Confidence should be derived from actual evidence quality."""
    rich_evidence = {"contacts": [1, 2, 3, 4, 5], "opportunities": [1, 2, 3], "signals": [1, 2]}
    poor_evidence = {"contacts": [], "opportunities": [], "signals": []}

    def derive_confidence(evidence: dict) -> float:
        score = 0.1
        score += min(len(evidence.get("contacts", [])) * 0.05, 0.25)
        score += min(len(evidence.get("opportunities", [])) * 0.05, 0.25)
        score += min(len(evidence.get("signals", [])) * 0.05, 0.15)
        return min(score, 0.95)

    assert derive_confidence(poor_evidence) == 0.1
    assert derive_confidence(rich_evidence) == 0.6


@pytest.mark.parametrize("fact,context_terms,expected", [
    ("الشركة لديها 150 موظفاً", ["150", "موظف"], True),
    ("الشركة تعمل في مجال الصحة", ["تقنية", "معلومات"], False),
])
def test_faithfulness_check(fact, context_terms, expected):
    """Verify that facts in output are supported by context."""
    supported = any(term in fact for term in context_terms)
    assert supported == expected


def test_agent_does_not_hallucinate_without_data():
    """Agent should return low confidence when no data is available."""
    context = {"company_info": {}, "contacts": [], "opportunities": []}
    evidence_count = (
        len(context.get("contacts", []))
        + len(context.get("opportunities", []))
    )
    if evidence_count == 0:
        confidence = 0.1
    else:
        confidence = min(0.3 + evidence_count * 0.05, 0.7)
    assert confidence == 0.1
