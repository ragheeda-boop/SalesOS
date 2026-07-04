"""Ranking pipeline — composable scoring stages.

Each stage is a pure function: candidates in → scored candidates out.
Stages run sequentially, accumulating scores.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from ..contracts.models import SearchQuery, SearchResult

T = TypeVar("T")


@dataclass
class ScoredItem(Generic[T]):
    item: T
    score: float = 0.0
    details: dict[str, float] = field(default_factory=dict)


class RankingStage(ABC, Generic[T]):
    """A single stage in the ranking pipeline."""

    name: str = ""

    @abstractmethod
    async def score(self, items: list[ScoredItem[T]], query: SearchQuery) -> list[ScoredItem[T]]: ...


class ExactMatchStage(RankingStage[T]):
    """Boost items where query matches key fields exactly."""

    name = "exact_match"
    fields: list[str]
    boost: float

    def __init__(self, fields: list[str] | None = None, boost: float = 10.0):
        self.fields = fields or []
        self.boost = boost

    async def score(self, items: list[ScoredItem[T]], query: SearchQuery) -> list[ScoredItem[T]]:
        q = query.query.lower().strip()
        if not q or not self.fields:
            return items

        for si in items:
            for field in self.fields:
                val = str(getattr(si.item, field, "")).lower()
                if val == q:
                    si.score += self.boost
                    si.details["exact_match"] = self.boost
                    break
        return items


class PartialMatchStage(RankingStage[T]):
    """Score based on how many tokens appear in relevant fields."""

    name = "partial_match"
    fields: list[str]
    weight: float

    def __init__(self, fields: list[str] | None = None, weight: float = 2.0):
        self.fields = fields or []
        self.weight = weight

    async def score(self, items: list[ScoredItem[T]], query: SearchQuery) -> list[ScoredItem[T]]:
        q = query.query.lower().strip()
        if not q or not self.fields:
            return items

        for si in items:
            match_count = 0
            for field in self.fields:
                val = str(getattr(si.item, field, "")).lower()
                if q in val:
                    match_count += 0.5
            if match_count > 0:
                si.score += match_count * self.weight
                si.details["partial_match"] = match_count * self.weight
        return items


class FreshnessStage(RankingStage[T]):
    """Boost recent items based on a date field."""

    name = "freshness"
    field: str
    weight: float

    def __init__(self, field: str = "created_at", weight: float = 1.0):
        self.field = field
        self.weight = weight

    async def score(self, items: list[ScoredItem[T]], query: SearchQuery) -> list[ScoredItem[T]]:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        for si in items:
            dt = getattr(si.item, self.field, None)
            if dt:
                age_hours = (now - dt).total_seconds() / 3600
                freshness = max(0, 1.0 - (age_hours / (30 * 24)))  # decay over 30 days
                si.score += freshness * self.weight
                si.details["freshness"] = freshness * self.weight
        return items


class TenantWeightStage(RankingStage[T]):
    """Apply tenant-specific weight if applicable."""

    name = "tenant_weight"
    weight: float

    def __init__(self, weight: float = 1.0):
        self.weight = weight

    async def score(self, items: list[ScoredItem[T]], query: SearchQuery) -> list[ScoredItem[T]]:
        # Future: use tenant profile to adjust scores
        return items


class RankingPipeline(Generic[T]):
    """Composable ranking pipeline.

    Stages run in order. Each stage receives scored items and returns them.
    """

    def __init__(self, stages: list[RankingStage[T]] | None = None):
        self._stages = stages or []

    def add_stage(self, stage: RankingStage[T]) -> RankingPipeline[T]:
        self._stages.append(stage)
        return self

    async def apply(self, query: SearchQuery, result: SearchResult[T]) -> SearchResult[T]:
        if not self._stages:
            return result

        scored = [ScoredItem(item=item) for item in result.items]

        for stage in self._stages:
            scored = await stage.score(scored, query)

        scored.sort(key=lambda x: x.score, reverse=True)
        result.items = [si.item for si in scored]
        result.ranking = [
            {"field": k, "score": v} for si in scored for k, v in si.details.items()
        ]

        return result

    @staticmethod
    def default(
        exact_fields: list[str] | None = None,
        partial_fields: list[str] | None = None,
    ) -> RankingPipeline:
        return RankingPipeline([
            ExactMatchStage(fields=exact_fields or ["name_ar", "name_en", "cr_number"]),
            PartialMatchStage(fields=partial_fields or ["name_ar", "name_en", "cr_number", "city"]),
            FreshnessStage(field="created_at"),
            TenantWeightStage(),
        ])
