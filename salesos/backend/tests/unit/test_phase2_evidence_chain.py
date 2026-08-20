"""Phase 2 Intelligence — Evidence chain domain tests.

Covers P2-6: Evidence chain (Insight → Evidence → Source → Timestamp → Confidence)
"""
from __future__ import annotations

import asyncio
import pytest

from domains.commercial.evidence.contracts.models import (
    Insight, InsightCategory, EvidenceItem, EvidenceType,
    EvidenceSource, ConfidenceLevel,
)
from domains.commercial.evidence.engine.service import EvidenceService
from domains.commercial.evidence.engine.in_memory_repo import InMemoryEvidenceRepository


@pytest.fixture
def repo():
    return InMemoryEvidenceRepository()


@pytest.fixture
def service(repo):
    return EvidenceService(repository=repo)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══ Model tests ═══

class TestEvidenceModels:

    def test_evidence_source_creation(self):
        src = EvidenceSource(source_domain="company", source_type="table_aggregate", source_id="c1", source_name="Company Table")
        assert src.source_domain == "company"
        assert src.source_id == "c1"

    def test_evidence_item_creation(self):
        src = EvidenceSource(source_domain="opportunity", source_type="event")
        item = EvidenceItem(
            id="e1", evidence_type=EvidenceType.BUSINESS_RULE,
            source=src, description="Deal value exceeds threshold",
            confidence=0.9, confidence_level=ConfidenceLevel.HIGH,
        )
        assert item.is_high_confidence
        assert item.evidence_type == EvidenceType.BUSINESS_RULE

    def test_evidence_item_low_confidence(self):
        src = EvidenceSource(source_domain="activity", source_type="observation")
        item = EvidenceItem(
            id="e2", evidence_type=EvidenceType.ACTIVITY_SIGNAL,
            source=src, description="Low activity", confidence=0.3,
            confidence_level=ConfidenceLevel.LOW,
        )
        assert not item.is_high_confidence

    def test_insight_creation(self):
        insight = Insight(
            id="i1", tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="Deal at risk", description="High churn probability",
            target_id="opp1", target_type="opportunity",
            overall_confidence=0.0, confidence_level=ConfidenceLevel.UNKNOWN,
        )
        assert insight.evidence_count == 0
        assert insight.confidence_level == ConfidenceLevel.UNKNOWN

    def test_insight_recompute_confidence(self):
        src = EvidenceSource(source_domain="company", source_type="rule")
        items = [
            EvidenceItem(id="e1", evidence_type=EvidenceType.BUSINESS_RULE, source=src,
                         description="Rule 1", confidence=0.9, confidence_level=ConfidenceLevel.HIGH),
            EvidenceItem(id="e2", evidence_type=EvidenceType.DATA_AGGREGATE, source=src,
                         description="Rule 2", confidence=0.7, confidence_level=ConfidenceLevel.MEDIUM),
        ]
        insight = Insight(
            id="i1", tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="Test", description="", target_id="c1", target_type="company",
            overall_confidence=0.0, confidence_level=ConfidenceLevel.UNKNOWN,
            evidence_items=items,
        )
        insight.recompute_confidence()
        assert insight.overall_confidence == 0.8
        assert insight.confidence_level == ConfidenceLevel.HIGH
        assert insight.evidence_count == 2
        assert len(insight.high_confidence_evidence) == 1

    def test_insight_recompute_no_evidence(self):
        insight = Insight(
            id="i1", tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="Empty", description="", target_id="c1", target_type="company",
            overall_confidence=0.5, confidence_level=ConfidenceLevel.MEDIUM,
        )
        insight.recompute_confidence()
        assert insight.overall_confidence == 0.0
        assert insight.confidence_level == ConfidenceLevel.UNKNOWN

    def test_insight_evidence_summary(self):
        src = EvidenceSource(source_domain="company", source_type="rule")
        items = [
            EvidenceItem(id="e1", evidence_type=EvidenceType.BUSINESS_RULE, source=src,
                         description="First evidence", confidence=0.8, confidence_level=ConfidenceLevel.HIGH),
            EvidenceItem(id="e2", evidence_type=EvidenceType.DATA_AGGREGATE, source=src,
                         description="Second evidence", confidence=0.6, confidence_level=ConfidenceLevel.MEDIUM),
        ]
        insight = Insight(
            id="i1", tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="Test", description="", target_id="c1", target_type="company",
            overall_confidence=0.0, confidence_level=ConfidenceLevel.UNKNOWN,
            evidence_items=items,
        )
        summary = insight.evidence_summary
        assert len(summary) == 2
        assert "First evidence" in summary
        assert "Second evidence" in summary


# ═══ Service tests ═══

class TestEvidenceService:

    def test_record_insight(self, service):
        insight = _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="Deal at risk", description="High churn",
            target_id="opp1", target_type="opportunity",
        ))
        assert insight.id
        assert insight.tenant_id == "t1"
        assert insight.category == InsightCategory.DEAL_RISK
        assert insight.overall_confidence == 0.0  # no evidence yet
        assert insight.confidence_level == ConfidenceLevel.UNKNOWN

    def test_record_insight_with_evidence(self, service):
        src = EvidenceSource(source_domain="opportunity", source_type="event")
        items = [
            EvidenceItem(id="e1", evidence_type=EvidenceType.PIPELINE_SIGNAL, source=src,
                         description="Stalled 30 days", confidence=0.85, confidence_level=ConfidenceLevel.HIGH),
        ]
        insight = _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="Deal stalled", description="", target_id="opp1",
            target_type="opportunity", evidence_items=items,
        ))
        assert insight.overall_confidence == 0.85
        assert insight.confidence_level == ConfidenceLevel.HIGH
        assert insight.evidence_count == 1

    def test_add_evidence_to_insight(self, service):
        insight = _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="Account review", description="", target_id="c1",
            target_type="company",
        ))
        evidence = _run(service.add_evidence(
            insight_id=insight.id, evidence_type=EvidenceType.ACTIVITY_SIGNAL,
            source_domain="activity", source_type="count",
            description="3 meetings this month", confidence=0.7,
        ))
        assert evidence.id
        assert evidence.confidence == 0.7
        assert evidence.confidence_level == ConfidenceLevel.MEDIUM
        updated = _run(service.get_insight(insight.id))
        assert updated.evidence_count == 1
        assert updated.overall_confidence == 0.7

    def test_add_evidence_to_missing_insight(self, service):
        with pytest.raises(ValueError, match="not found"):
            _run(service.add_evidence(
                insight_id="nonexistent", evidence_type=EvidenceType.BUSINESS_RULE,
                source_domain="company", source_type="rule",
                description="test", confidence=0.5,
            ))

    def test_list_insights(self, service):
        _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="Risk 1", description="", target_id="opp1", target_type="opportunity",
        ))
        _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="Health 1", description="", target_id="c1", target_type="company",
        ))
        _run(service.record_insight(
            tenant_id="t2", category=InsightCategory.DEAL_RISK,
            title="Other tenant", description="", target_id="opp2", target_type="opportunity",
        ))
        all_t1 = _run(service.list_insights("t1"))
        assert len(all_t1) == 2
        risks_only = _run(service.list_insights("t1", category=InsightCategory.DEAL_RISK))
        assert len(risks_only) == 1
        assert risks_only[0].title == "Risk 1"

    def test_list_high_confidence(self, service):
        src = EvidenceSource(source_domain="company", source_type="rule")
        high_items = [EvidenceItem(id="e1", evidence_type=EvidenceType.BUSINESS_RULE, source=src,
                                   description="High", confidence=0.9, confidence_level=ConfidenceLevel.HIGH)]
        low_items = [EvidenceItem(id="e2", evidence_type=EvidenceType.BUSINESS_RULE, source=src,
                                  description="Low", confidence=0.3, confidence_level=ConfidenceLevel.LOW)]
        _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="High conf", description="", target_id="opp1", target_type="opportunity",
            evidence_items=high_items,
        ))
        _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="Low conf", description="", target_id="c1", target_type="company",
            evidence_items=low_items,
        ))
        high = _run(service.list_high_confidence("t1"))
        assert len(high) == 1
        assert high[0].title == "High conf"

    def test_kpis(self, service):
        src = EvidenceSource(source_domain="company", source_type="rule")
        high_items = [EvidenceItem(id="e1", evidence_type=EvidenceType.BUSINESS_RULE, source=src,
                                   description="High", confidence=0.9, confidence_level=ConfidenceLevel.HIGH)]
        _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="Risk 1", description="", target_id="opp1", target_type="opportunity",
            evidence_items=high_items,
        ))
        _run(service.record_insight(
            tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="Health 1", description="", target_id="c1", target_type="company",
        ))
        kpis = _run(service.kpis("t1"))
        assert kpis["total"] == 2
        assert kpis["by_category"]["deal_risk"] == 1
        assert kpis["by_category"]["account_health"] == 1
        assert kpis["high_confidence"] == 1

    def test_confidence_level_mapping(self):
        assert EvidenceService._confidence_level(0.95) == ConfidenceLevel.HIGH
        assert EvidenceService._confidence_level(0.8) == ConfidenceLevel.HIGH
        assert EvidenceService._confidence_level(0.6) == ConfidenceLevel.MEDIUM
        assert EvidenceService._confidence_level(0.5) == ConfidenceLevel.MEDIUM
        assert EvidenceService._confidence_level(0.3) == ConfidenceLevel.LOW
        assert EvidenceService._confidence_level(0.2) == ConfidenceLevel.LOW
        assert EvidenceService._confidence_level(0.1) == ConfidenceLevel.UNKNOWN


# ═══ Repository tests ═══

class TestInMemoryEvidenceRepository:

    def test_save_and_get_insight(self, repo):
        insight = Insight(
            id="i1", tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="Test", description="", target_id="opp1", target_type="opportunity",
            overall_confidence=0.5, confidence_level=ConfidenceLevel.MEDIUM,
        )
        _run(repo.save_insight(insight))
        fetched = _run(repo.get_insight("i1"))
        assert fetched is not None
        assert fetched.title == "Test"

    def test_get_missing_insight(self, repo):
        assert _run(repo.get_insight("nonexistent")) is None

    def test_list_by_target(self, repo):
        for i in range(3):
            _run(repo.save_insight(Insight(
                id=f"i{i}", tenant_id="t1", category=InsightCategory.DEAL_RISK,
                title=f"Risk {i}", description="", target_id="opp1", target_type="opportunity",
                overall_confidence=0.5, confidence_level=ConfidenceLevel.MEDIUM,
            )))
        results = _run(repo.list_insights("t1", target_id="opp1"))
        assert len(results) == 3

    def test_count_by_category(self, repo):
        _run(repo.save_insight(Insight(
            id="i1", tenant_id="t1", category=InsightCategory.DEAL_RISK,
            title="R", description="", target_id="o1", target_type="opportunity",
            overall_confidence=0.5, confidence_level=ConfidenceLevel.MEDIUM,
        )))
        _run(repo.save_insight(Insight(
            id="i2", tenant_id="t1", category=InsightCategory.ACCOUNT_HEALTH,
            title="H", description="", target_id="c1", target_type="company",
            overall_confidence=0.5, confidence_level=ConfidenceLevel.MEDIUM,
        )))
        counts = _run(repo.count_by_category("t1"))
        assert counts["deal_risk"] == 1
        assert counts["account_health"] == 1
