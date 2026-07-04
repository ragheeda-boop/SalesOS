"""Tests for RankingPipeline — ExactMatch, PartialMatch, Freshness, and full pipeline."""

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

import pytest

from domains.search.contracts.models import SearchQuery, SearchResult
from domains.search.ranking.pipeline import (
    ExactMatchStage,
    FreshnessStage,
    PartialMatchStage,
    RankingPipeline,
    ScoredItem,
    TenantWeightStage,
)


@dataclass
class FakeCompany:
    name_ar: str = ""
    name_en: str = ""
    cr_number: str = ""
    city: str = ""
    activity_description: str = ""
    created_at: datetime | None = None


@pytest.mark.asyncio
async def test_exact_match_stage_boost():
    stage = ExactMatchStage(fields=["name_ar", "cr_number"], boost=10.0)
    items = [
        ScoredItem(item=FakeCompany(name_ar="شركة الأمل", cr_number="CR-100")),
        ScoredItem(item=FakeCompany(name_ar="شركة النور", cr_number="CR-200")),
    ]
    query = SearchQuery(query="CR-100")
    result = await stage.score(items, query)
    assert result[0].score == 10.0
    assert result[0].details.get("exact_match") == 10.0
    assert result[1].score == 0.0


@pytest.mark.asyncio
async def test_exact_match_arabic():
    stage = ExactMatchStage(fields=["name_ar"], boost=10.0)
    items = [
        ScoredItem(item=FakeCompany(name_ar="شركة الأمل")),
        ScoredItem(item=FakeCompany(name_ar="شركة النور")),
    ]
    query = SearchQuery(query="شركة الأمل")
    result = await stage.score(items, query)
    assert result[0].score == 10.0
    assert result[1].score == 0.0


@pytest.mark.asyncio
async def test_partial_match_stage():
    stage = PartialMatchStage(fields=["name_ar", "city"], weight=2.0)
    items = [
        ScoredItem(item=FakeCompany(name_ar="شركة الأمل للنقل", city="الرياض")),
        ScoredItem(item=FakeCompany(name_ar="مؤسسة السلام", city="جدة")),
    ]
    query = SearchQuery(query="نقل")
    result = await stage.score(items, query)
    assert result[0].score > 0
    assert result[1].score == 0.0


@pytest.mark.asyncio
async def test_freshness_stage_recent_boosted():
    now = datetime.now(timezone.utc)
    recent = FakeCompany(name_ar="جديد", created_at=now - timedelta(hours=1))
    old = FakeCompany(name_ar="قديم", created_at=now - timedelta(days=60))
    items = [ScoredItem(item=recent), ScoredItem(item=old)]
    query = SearchQuery(query="test")
    stage = FreshnessStage(field="created_at", weight=1.0)
    result = await stage.score(items, query)
    assert result[0].score > result[1].score


@pytest.mark.asyncio
async def test_tenant_weight_stage_noop():
    stage = TenantWeightStage()
    items = [ScoredItem(item=FakeCompany(name_ar="Test"))]
    query = SearchQuery(query="test")
    result = await stage.score(items, query)
    assert result[0].score == 0.0


@pytest.mark.asyncio
async def test_ranking_pipeline_full():
    pipeline = RankingPipeline([
        ExactMatchStage(fields=["name_ar"], boost=10.0),
        PartialMatchStage(fields=["name_ar", "city"], weight=2.0),
    ])
    query = SearchQuery(query="شركة الأمل")
    result = SearchResult(
        items=[
            FakeCompany(name_ar="شركة النور", city="جدة"),
            FakeCompany(name_ar="شركة الأمل للنقل", city="الرياض"),
            FakeCompany(name_ar="مؤسسة السلام", city="جدة"),
        ]
    )
    final = await pipeline.apply(query, result)
    assert final.items[0].name_ar == "شركة الأمل للنقل"


@pytest.mark.asyncio
async def test_ranking_pipeline_empty_pipeline():
    pipeline = RankingPipeline()
    query = SearchQuery(query="test")
    result = SearchResult(items=[FakeCompany(name_ar="Test")])
    final = await pipeline.apply(query, result)
    assert len(final.items) == 1
    assert final.items[0].name_ar == "Test"


@pytest.mark.asyncio
async def test_ranking_pipeline_empty_query():
    stage = ExactMatchStage(fields=["name_ar"], boost=10.0)
    items = [ScoredItem(item=FakeCompany(name_ar="شركة"))]
    query = SearchQuery(query="")
    result = await stage.score(items, query)
    assert result[0].score == 0.0


def test_ranking_pipeline_default():
    pipeline = RankingPipeline.default(
        exact_fields=["name_ar"],
        partial_fields=["name_ar", "city"],
    )
    assert pipeline is not None
    assert len(pipeline._stages) == 4
