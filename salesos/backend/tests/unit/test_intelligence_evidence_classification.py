from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from domains.commercial.evidence.contracts.models import EvidenceKind
from intelligence.account_intelligence import AccountHealth, AccountIntelligenceService
from intelligence.deal_intelligence import DealHealth, DealIntelligenceService


@pytest.mark.asyncio
async def test_account_insight_labels_crm_aggregates_as_one_nonprimary_source():
    evidence_service = SimpleNamespace(
        record_insight=AsyncMock(return_value=SimpleNamespace(id="insight-1")),
    )
    service = AccountIntelligenceService(evidence_service, memory_service=None)
    health = AccountHealth(
        account_id="company-1",
        account_name="Example Co",
        health_score=0.6,
        health_level="at_risk",
        total_opportunities=2,
        won_deals=1,
        lost_deals=1,
        total_revenue=1000,
        activity_frequency=3,
    )

    await service.record_account_insight("tenant-1", "company-1", "Example Co", health)

    evidence = evidence_service.record_insight.call_args.kwargs["evidence_items"]
    assert len(evidence) == 4
    assert {item.evidence_kind for item in evidence} == {EvidenceKind.CRM_SYSTEM_RECORD}
    assert {item.source.source_id for item in evidence} == {"company-1"}
    assert {item.source.source_name for item in evidence} == {"SalesOS CRM"}


@pytest.mark.asyncio
async def test_deal_insight_labels_crm_factors_as_one_nonprimary_source():
    evidence_service = SimpleNamespace(
        record_insight=AsyncMock(return_value=SimpleNamespace(id="insight-2")),
    )
    service = DealIntelligenceService(evidence_service, memory_service=None)
    health = DealHealth(
        deal_id="opportunity-1",
        deal_name="Example Deal",
        health_score=0.5,
        health_level="at_risk",
        risk_factors=["No activities recorded"],
        opportunity_factors=["High probability"],
        stage="proposal",
        value=10000,
        probability=0.6,
    )

    await service.record_deal_insight("tenant-1", "opportunity-1", "Example Deal", health)

    evidence = evidence_service.record_insight.call_args.kwargs["evidence_items"]
    assert len(evidence) == 3
    assert {item.evidence_kind for item in evidence} == {EvidenceKind.CRM_SYSTEM_RECORD}
    assert {item.source.source_id for item in evidence} == {"opportunity-1"}
    assert {item.source.source_name for item in evidence} == {"SalesOS CRM"}
