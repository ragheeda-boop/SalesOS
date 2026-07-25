"""Grounding service tests — AgentContext and GroundingService."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from intelligence.grounding import AgentContext, GroundingService


def test_agent_context_is_empty():
    ctx = AgentContext()
    assert ctx.is_empty() is True


def test_agent_context_not_empty():
    ctx = AgentContext(company_info={"name_ar": "شركة"})
    assert ctx.is_empty() is False


def test_agent_context_not_empty_contacts():
    ctx = AgentContext(contacts=[{"name": "Ahmed"}])
    assert ctx.is_empty() is False


def test_to_prompt_block_empty():
    ctx = AgentContext()
    block = ctx.to_prompt_block()
    assert "بيانات" in block
    assert "للسياق" in block
    assert "مُسترجعة" in block or "مسترجعة" in block


def test_to_prompt_block_with_company():
    ctx = AgentContext(company_info={"name_ar": "شركة التقنية", "city": "الرياض"})
    block = ctx.to_prompt_block()
    assert "شركة التقنية" in block
    assert "الرياض" in block


def test_to_prompt_block_with_contacts():
    ctx = AgentContext(contacts=[{"name": "Ahmed"}, {"name": "Sara"}])
    block = ctx.to_prompt_block()
    assert "Ahmed" in block
    assert "Sara" in block


def test_to_prompt_block_with_opportunities():
    ctx = AgentContext(opportunities=[{"stage": "qualified", "amount": "50000"}])
    block = ctx.to_prompt_block()
    assert "qualified" in block
    assert "50000" in block or "50000" in block


def test_to_prompt_block_with_signals():
    ctx = AgentContext(signals=[{"title": "New tender"}])
    block = ctx.to_prompt_block()
    assert "New tender" in block


def test_to_prompt_block_with_activity():
    ctx = AgentContext(recent_activity=[{"description": "Email sent"}])
    block = ctx.to_prompt_block()
    assert "Email sent" in block


def test_to_prompt_block_with_relationships():
    ctx = AgentContext(relationships=[{"target_name": "Partner Co"}])
    block = ctx.to_prompt_block()
    assert "Partner Co" in block


def test_to_prompt_block_max_contacts():
    contacts = [{"name": f"User {i}"} for i in range(20)]
    ctx = AgentContext(contacts=contacts)
    block = ctx.to_prompt_block()
    count = block.count("User")
    assert count <= 6


@pytest.mark.asyncio
async def test_grounding_service_get_context_no_deps():
    svc = GroundingService()
    ctx = await svc.get_context("company-1")
    assert isinstance(ctx, AgentContext)
    assert ctx.is_empty() is True


@pytest.mark.asyncio
async def test_grounding_service_get_context_with_db():
    mock_factory = MagicMock()
    mock_session = AsyncMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    mock_row = MagicMock()
    mock_row.mappings.return_value.first.return_value = {"name_ar": "شركة", "city": "الرياض"}
    mock_session.execute.return_value = mock_row

    svc = GroundingService(db_session_factory=mock_factory)
    ctx = await svc.get_context("company-1")
    assert ctx.company_info is not None


@pytest.mark.asyncio
async def test_grounding_service_get_context_db_error():
    mock_factory = MagicMock()
    mock_factory.side_effect = Exception("DB error")

    svc = GroundingService(db_session_factory=mock_factory)
    ctx = await svc.get_context("company-1")
    assert isinstance(ctx, AgentContext)


def test_grounding_service_init():
    svc = GroundingService()
    assert svc._db_session_factory is None
    assert svc._neo4j_driver is None


def test_grounding_service_init_with_deps():
    svc = GroundingService(db_session_factory=MagicMock(), neo4j_driver=MagicMock())
    assert svc._db_session_factory is not None
    assert svc._neo4j_driver is not None
