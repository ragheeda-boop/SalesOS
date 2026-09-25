from __future__ import annotations

import json
from pathlib import Path

import pytest

from domains.commercial.evidence.contracts.models import (
    ConfidenceLevel,
    EvidenceBand,
    EvidenceItem,
    EvidenceKind,
    EvidenceSource,
    EvidenceType,
    Insight,
    InsightCategory,
)
from domains.commercial.evidence.engine.scoring import decide_fact, score_evidence
from domains.commercial.infrastructure.postgres_repositories import PostgresEvidenceRepository

EXPECTED_OFFICIAL_REGISTRY_WEIGHT = 0.98
EXPECTED_COMBINED_SCORE = 0.99
EXPECTED_COMBINED_UNCAPPED_SCORE = 0.996
EXPECTED_CONTRADICTION_CAP = 0.45
EXPECTED_MIXED_COMPATIBILITY_SCORE = 0.46


class _FakeSession:
    def __init__(self):
        self.added = []

    def add(self, model):
        self.added.append(model)

    async def flush(self):
        return None


def _item(kind: EvidenceKind, source_id: str, confidence: float = 0.01) -> EvidenceItem:
    return EvidenceItem(
        id=f"evidence-{source_id}-{kind.value}",
        evidence_type=EvidenceType.DATA_AGGREGATE,
        source=EvidenceSource(
            source_domain="registry" if kind == EvidenceKind.OFFICIAL_REGISTRY else "web",
            source_type="document",
            source_id=source_id,
            source_name=source_id,
        ),
        description="Test evidence",
        confidence=confidence,
        confidence_level=ConfidenceLevel.UNKNOWN,
        evidence_kind=kind,
    )


def test_bayesian_score_uses_kind_weight_and_ignores_model_confidence():
    low_model_confidence = _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1", 0.01)
    high_model_confidence = _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1", 0.99)

    result = score_evidence([low_model_confidence, high_model_confidence])

    assert result.score == EXPECTED_OFFICIAL_REGISTRY_WEIGHT
    assert result.primary_source_count == 1
    assert result.evidence_count == 1


def test_independent_sources_combine_with_noisy_or_and_cap_at_point_99():
    items = [
        _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1"),
        _item(EvidenceKind.CRM_EMAIL_SIGNATURE, "crm-2"),
    ]

    result = score_evidence(items)

    assert result.score == EXPECTED_COMBINED_SCORE
    assert result.uncapped_score == EXPECTED_COMBINED_UNCAPPED_SCORE


def test_shared_python_typescript_golden_vectors():
    repo_root = Path(__file__).resolve().parents[3]
    vectors_path = (
        repo_root
        / "packages"
        / "platform"
        / "decision"
        / "evidence-engine"
        / "adr0113-golden.json"
    )
    golden_cases = json.loads(vectors_path.read_text(encoding="utf-8"))["cases"]

    for case in golden_cases:
        items = [
            EvidenceItem(
                id=item["id"],
                evidence_type=EvidenceType.DATA_AGGREGATE,
                source=EvidenceSource(
                    source_domain="golden",
                    source_type="record",
                    source_id=item.get("source_id", ""),
                ),
                description=case["name"],
                confidence=item["confidence"],
                confidence_level=ConfidenceLevel.UNKNOWN,
                evidence_kind=(
                    EvidenceKind(item["evidence_kind"])
                    if item.get("evidence_kind")
                    else None
                ),
            )
            for item in case["items"]
        ]
        actual = score_evidence(items)
        assert actual.score == case["expected"]["score"], case["name"]
        assert actual.uncapped_score == case["expected"]["uncapped_score"], case["name"]
        assert (
            actual.contradiction_present == case["expected"]["contradiction_present"]
        ), case["name"]
        assert (
            actual.primary_source_count == case["expected"]["primary_source_count"]
        ), case["name"]
        assert actual.evidence_count == case["expected"]["evidence_count"], case["name"]


def test_contradiction_caps_combined_strength_at_point_45():
    items = [
        _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1"),
        _item(EvidenceKind.CONTRADICTION, "audit-2"),
    ]

    result = score_evidence(items)

    assert result.uncapped_score == EXPECTED_OFFICIAL_REGISTRY_WEIGHT
    assert result.score == EXPECTED_CONTRADICTION_CAP
    assert result.contradiction_present is True


def test_cr_exact_match_can_be_verified_from_one_primary_source():
    decision = decide_fact(
        "cr_number",
        [_item(EvidenceKind.CR_NUMBER_EXACT_MATCH, "source-1")],
    )

    # ADR-0114 prohibits agent writes to identity fields, so retain the
    # verified candidate for human approval instead of applying it.
    assert decision.band == EvidenceBand.VERIFIED
    assert decision.store is True
    assert decision.auto_apply is False
    assert decision.approval_required is True
    assert decision.reason == "identity_field_requires_human_review"


def test_mixed_typed_and_legacy_evidence_cannot_make_a_fact_decision():
    typed = _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1")
    legacy = _item(EvidenceKind.OFFICIAL_REGISTRY, "legacy-2")
    legacy.evidence_kind = None

    decision = decide_fact("city", [typed, legacy])

    assert decision.band == EvidenceBand.DISCARD
    assert decision.store is False
    assert decision.auto_apply is False
    assert decision.reason == "unclassified_evidence_not_eligible_for_fact_decision"


def test_unknown_field_needs_review_even_with_verified_evidence():
    decision = decide_fact(
        "new_unreviewed_field",
        [_item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1")],
    )

    assert decision.band == EvidenceBand.VERIFIED
    assert decision.store is True
    assert decision.auto_apply is False
    assert decision.approval_required is True
    assert decision.reason == "field_not_allowlisted_for_auto_apply"


def test_crm_system_record_is_probable_non_primary_evidence():
    item = _item(EvidenceKind.CRM_SYSTEM_RECORD, "crm-company-1", confidence=0.99)

    result = score_evidence([item])
    decision = decide_fact("industry", [item])

    assert result.score == 0.55
    assert result.primary_source_count == 0
    assert decision.band == EvidenceBand.PROBABLE
    assert decision.auto_apply is False


def test_industry_requires_two_primary_sources_for_verified_band():
    one_source = decide_fact(
        "industry",
        [_item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1")],
    )
    two_sources = decide_fact(
        "industry",
        [
            _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1"),
            _item(EvidenceKind.GOVERNMENT_SOURCE, "government-2"),
        ],
    )

    assert one_source.band == EvidenceBand.PROBABLE
    assert one_source.auto_apply is False
    assert two_sources.band == EvidenceBand.VERIFIED
    assert two_sources.auto_apply is True


def test_employees_count_is_always_proposed_even_with_strong_evidence():
    decision = decide_fact(
        "employees_count",
        [_item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1")],
    )

    assert decision.band == EvidenceBand.VERIFIED
    assert decision.store is True
    assert decision.auto_apply is False
    assert decision.approval_required is True


def test_insight_uses_typed_evidence_strength_not_model_confidence():
    insight = Insight(
        id="insight-1",
        tenant_id="tenant-1",
        category=InsightCategory.ACCOUNT_HEALTH,
        title="Verified registration",
        description="",
        target_id="company-1",
        target_type="company",
        overall_confidence=0.0,
        confidence_level=ConfidenceLevel.UNKNOWN,
        evidence_items=[_item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1", 0.02)],
    )

    insight.recompute_confidence()

    assert insight.overall_confidence == EXPECTED_OFFICIAL_REGISTRY_WEIGHT
    assert insight.confidence_level == ConfidenceLevel.HIGH
    assert insight.high_confidence_evidence == insight.evidence_items
    assert insight.metadata["evidence_score_method"] == "adr_0113_bayesian_v1"


def test_mixed_typed_and_legacy_evidence_keeps_all_items_in_compatibility_score():
    typed = _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1", confidence=0.02)
    legacy = EvidenceItem(
        id="legacy-evidence",
        evidence_type=EvidenceType.DATA_AGGREGATE,
        source=EvidenceSource(source_domain="legacy", source_type="record"),
        description="Unclassified existing evidence",
        confidence=0.9,
        confidence_level=ConfidenceLevel.HIGH,
    )
    insight = Insight(
        id="insight-mixed",
        tenant_id="tenant-1",
        category=InsightCategory.ACCOUNT_HEALTH,
        title="Mixed evidence",
        description="",
        target_id="company-1",
        target_type="company",
        overall_confidence=0.0,
        confidence_level=ConfidenceLevel.UNKNOWN,
        evidence_items=[typed, legacy],
    )

    insight.recompute_confidence()

    assert insight.overall_confidence == EXPECTED_MIXED_COMPATIBILITY_SCORE
    assert insight.metadata["evidence_score_method"] == "legacy_average_compatibility"
    assert "evidence_contradiction_present" not in insight.metadata


def test_legacy_recalculation_clears_a_stale_typed_contradiction_flag():
    insight = Insight(
        id="insight-2",
        tenant_id="tenant-1",
        category=InsightCategory.ACCOUNT_HEALTH,
        title="Existing evidence",
        description="",
        target_id="company-1",
        target_type="company",
        overall_confidence=0.0,
        confidence_level=ConfidenceLevel.UNKNOWN,
        evidence_items=[
            EvidenceItem(
                id="legacy-evidence",
                evidence_type=EvidenceType.DATA_AGGREGATE,
                source=EvidenceSource(source_domain="legacy", source_type="record"),
                description="Unclassified existing evidence",
                confidence=0.6,
                confidence_level=ConfidenceLevel.MEDIUM,
            )
        ],
        metadata={"evidence_contradiction_present": True},
    )

    insight.recompute_confidence()

    assert insight.metadata["evidence_score_method"] == "legacy_average_compatibility"
    assert "evidence_contradiction_present" not in insight.metadata


@pytest.mark.asyncio
async def test_evidence_kind_round_trips_through_existing_json_data_column():
    session = _FakeSession()
    repository = PostgresEvidenceRepository(session)
    source_item = _item(EvidenceKind.OFFICIAL_REGISTRY, "registry-1")

    await repository.save_evidence("insight-1", source_item)
    saved_model = session.added[0]
    restored = repository._evidence_to_domain(saved_model)

    assert saved_model.extra_data["evidence_kind"] == EvidenceKind.OFFICIAL_REGISTRY.value
    assert restored.evidence_kind == EvidenceKind.OFFICIAL_REGISTRY
    assert restored.data == {}
