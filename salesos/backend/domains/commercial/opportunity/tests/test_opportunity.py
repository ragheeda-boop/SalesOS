"""Tests for Opportunity Domain."""

from datetime import date, datetime, timedelta, timezone

import pytest

from domains.commercial.opportunity.contracts.models import (
    Opportunity,
    OpportunityStage,
    OpportunityStatus,
    PipelineDefinition,
)
from domains.commercial.opportunity.contracts.repository import OpportunityQuery
from domains.commercial.opportunity.engine.in_memory_repo import (
    InMemoryOpportunityRepository,
)
from domains.commercial.opportunity.engine.service import OpportunityService


def test_default_pipeline():
    stages = OpportunityStage.default_pipeline()
    assert len(stages) == 6
    assert stages[0].name == "prospecting"
    assert stages[4].name == "closed_won"
    assert stages[4].is_terminal
    assert stages[5].name == "closed_lost"


def test_pipeline_transition_valid():
    pipe = PipelineDefinition(tenant_id="t1")
    assert pipe.is_valid_transition("prospecting", "qualification")
    assert pipe.is_valid_transition("qualification", "proposal")
    assert pipe.is_valid_transition("proposal", "negotiation")
    assert pipe.is_valid_transition("negotiation", "closed_won")
    assert pipe.is_valid_transition("negotiation", "closed_lost")


def test_pipeline_transition_invalid():
    pipe = PipelineDefinition(tenant_id="t1")
    assert not pipe.is_valid_transition("closed_won", "negotiation")
    assert not pipe.is_valid_transition("closed_lost", "negotiation")
    assert not pipe.is_valid_transition("negotiation", "nonexistent")


def test_pipeline_transition_recycle():
    """Recycling to first stage is permitted."""
    pipe = PipelineDefinition(tenant_id="t1")
    assert pipe.is_valid_transition("qualification", "prospecting")


def test_opportunity_weighted_value():
    opp = Opportunity(id="1", tenant_id="t1", company_id="c1", name="Deal", value=100000, probability=0.5)
    assert opp.weighted_value == 50000.0


def test_opportunity_is_terminal():
    open_opp = Opportunity(id="1", tenant_id="t1", company_id="c1", name="Open")
    won_opp = Opportunity(id="2", tenant_id="t1", company_id="c1", name="Won", status=OpportunityStatus.WON)
    lost_opp = Opportunity(id="3", tenant_id="t1", company_id="c1", name="Lost", status=OpportunityStatus.LOST)

    assert not open_opp.is_terminal
    assert won_opp.is_terminal
    assert lost_opp.is_terminal


@pytest.mark.asyncio
async def test_create_opportunity():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity(
        tenant_id="t1",
        company_id="c1",
        name="صفقة كبرى",
        value=500000,
        owner_id="user-1",
        expected_close_date=date(2026, 12, 31),
    )
    assert opp.name == "صفقة كبرى"
    assert opp.stage == "prospecting"
    assert opp.probability == 0.10
    assert opp.tenant_id == "t1"
    assert opp.status == OpportunityStatus.OPEN


@pytest.mark.asyncio
async def test_advance_stage():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity("t1", "c1", "Deal", value=100000)

    opp = await service.advance_stage(opp.id, "qualification")
    assert opp.stage == "qualification"
    assert opp.probability == 0.25

    opp = await service.advance_stage(opp.id, "proposal")
    assert opp.stage == "proposal"
    assert opp.probability == 0.50


@pytest.mark.asyncio
async def test_close_won():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity("t1", "c1", "Deal", value=100000)
    opp = await service.advance_stage(opp.id, "negotiation")
    opp = await service.close_won(opp.id, won_amount=120000)

    assert opp.status == OpportunityStatus.WON
    assert opp.stage == "closed_won"
    assert opp.won_amount == 120000
    assert opp.is_terminal


@pytest.mark.asyncio
async def test_close_lost():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity("t1", "c1", "Lost Deal", value=50000)
    opp = await service.advance_stage(opp.id, "negotiation")
    opp = await service.close_lost(opp.id, loss_reason="العميل اختار منافس")

    assert opp.status == OpportunityStatus.LOST
    assert opp.loss_reason == "العميل اختار منافس"
    assert opp.probability == 0.0
    assert opp.is_terminal


@pytest.mark.asyncio
async def test_cannot_change_terminal_value():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity("t1", "c1", "Deal", value=100000)
    await service.advance_stage(opp.id, "negotiation")
    await service.close_won(opp.id)

    with pytest.raises(ValueError, match="closed opportunity"):
        await service.update_value(opp.id, 200000)


@pytest.mark.asyncio
async def test_invalid_stage_transition():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity("t1", "c1", "Deal")
    await service.advance_stage(opp.id, "closed_won")

    with pytest.raises(ValueError, match="Invalid stage transition"):
        await service.advance_stage(opp.id, "negotiation")


@pytest.mark.asyncio
async def test_query_by_stage():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    for i in range(5):
        opp = await service.create_opportunity("t1", f"c{i}", f"Deal {i}")
        if i < 2:
            await service.advance_stage(opp.id, "qualification")
        if i < 1:
            await service.advance_stage(opp.id, "proposal")

    result = await service.query(OpportunityQuery(tenant_id="t1", stage="qualification"))
    assert result.total == 1  # deal 0 advanced further to proposal


@pytest.mark.asyncio
async def test_count_by_stage():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    for i in range(10):
        opp = await service.create_opportunity("t1", f"c{i}", f"Deal {i}")
        if i < 5:
            await service.advance_stage(opp.id, "qualification")
        if i < 2:
            await service.advance_stage(opp.id, "proposal")

    counts = await service.count_by_stage("t1")
    assert counts.get("prospecting", 0) == 5
    assert counts.get("qualification", 0) == 3
    assert counts.get("proposal", 0) == 2


@pytest.mark.asyncio
async def test_pipeline_summary():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity("t1", "c1", "Big Deal", value=1000000)
    await service.advance_stage(opp.id, "negotiation")

    summary = await service.pipeline_summary("t1")
    assert summary["stages"]["negotiation"]["count"] == 1
    assert summary["stages"]["negotiation"]["total_value"] == 1000000
    assert summary["total_pipeline_value"] == 1000000


@pytest.mark.asyncio
async def test_win_rate():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    for i in range(10):
        opp = await service.create_opportunity("t1", f"c{i}", f"Deal {i}")
        if i < 6:
            await service.close_won(opp.id)
        elif i < 8:
            await service.close_lost(opp.id)

    rate = await service.win_rate("t1")
    assert rate == 0.75  # 6 won / 8 closed


@pytest.mark.asyncio
async def test_recycle_stage():
    repo = InMemoryOpportunityRepository()
    service = OpportunityService(repository=repo)

    opp = await service.create_opportunity("t1", "c1", "Recycle Deal")
    await service.advance_stage(opp.id, "qualification")

    # Recycle back to prospecting is valid
    opp = await service.advance_stage(opp.id, "prospecting")
    assert opp.stage == "prospecting"
