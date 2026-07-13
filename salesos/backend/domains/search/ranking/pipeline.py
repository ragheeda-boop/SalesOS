"""Ranking pipeline — composable scoring stages.

Each stage is a pure function: candidates in → scored candidates out.
Stages run sequentially, accumulating scores.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, TypeVar

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


class ArabicNameMatchStage(RankingStage[T]):
    """Boost exact Arabic name matches and handle transliteration.

    - Boosts exact Arabic name matches significantly
    - Handles transliteration (Arabic ↔ English name variants)
    - Applies fuzzy matching for common misspellings
    - Weights city/region matches higher for local businesses
    """

    name = "arabic_name_match"

    # Common Arabic-English transliteration pairs for company names
    TRANSLITERATION_MAP: ClassVar[dict[str, set[str]]] = {
        "شركة": {"sharika", "company", "co"},
        "مؤسسة": {"muassasa", "foundation", "establishment"},
        "مصنع": {"masna", "factory", "manufacturing"},
        "مجموعة": {"majmua", "group"},
        "الرياض": {"riyadh", "riyad"},
        "جدة": {"jeddah", "jaddah", "jedda"},
        "الدمام": {"dammam", "dammam"},
        "مكة": {"makkah", "makkah"},
        "المدينة": {"madinah", "medina"},
        "أرامكو": {"aramco", "aramco"},
        "المراعي": {"almarai", "al-marai"},
        "جرير": {"jarir", "jarir"},
        "البنك": {"bank", "bank"},
        "السعودي": {"saudi", "saudia"},
    }

    # Common Arabic misspellings
    MISSPELLING_MAP: ClassVar[dict[str, str]] = {
        "شركه": "شركة",
        "مؤسسه": "مؤسسة",
        "مصنعه": "مصنع",
        "مجوعة": "مجموعة",
        "الرياضه": "الرياض",
        "جده": "جدة",
        "الدمامه": "الدمام",
        "الرسيم": "الرسمي",
        "التجاري": "التجاري",
    }

    CITY_BOOST: ClassVar[float] = 3.0
    REGION_BOOST: ClassVar[float] = 2.0
    ARABIC_NAME_EXACT_BOOST: ClassVar[float] = 15.0
    ARABIC_NAME_PARTIAL_BOOST: ClassVar[float] = 8.0
    TRANSLITERATION_BOOST: ClassVar[float] = 5.0
    FUZZY_BOOST: ClassVar[float] = 3.0

    def __init__(self, arabic_fields: list[str] | None = None, english_fields: list[str] | None = None):
        self.arabic_fields = arabic_fields or ["name_ar"]
        self.english_fields = english_fields or ["name_en"]
        self._normalizer = None

    @property
    def normalizer(self):
        if self._normalizer is None:
            from ..normalization import ArabicSearchNormalizer
            self._normalizer = ArabicSearchNormalizer.for_matching()
        return self._normalizer

    async def score(self, items: list[ScoredItem[T]], query: SearchQuery) -> list[ScoredItem[T]]:
        q_raw = query.query.strip()
        if not q_raw:
            return items

        q_normalized = self.normalizer.normalize(q_raw)
        q_lower = q_raw.lower().strip()

        for si in items:
            # 1. Exact Arabic name match
            for field in self.arabic_fields:
                val = str(getattr(si.item, field, "")).strip()
                val_normalized = self.normalizer.normalize(val)
                if val_normalized and q_normalized == val_normalized:
                    si.score += self.ARABIC_NAME_EXACT_BOOST
                    si.details["arabic_exact"] = self.ARABIC_NAME_EXACT_BOOST
                    break
                elif val_normalized and q_normalized in val_normalized:
                    si.score += self.ARABIC_NAME_PARTIAL_BOOST
                    si.details["arabic_partial"] = self.ARABIC_NAME_PARTIAL_BOOST
                    break

            # 2. Transliteration match (Arabic query vs English name or vice versa)
            for eng_field in self.english_fields:
                eng_val = str(getattr(si.item, eng_field, "")).lower().strip()
                if not eng_val:
                    continue

                # Check if query or any query token matches transliteration
                query_tokens = q_lower.split()
                for token in query_tokens:
                    for arabic_key, english_variants in self.TRANSLITERATION_MAP.items():
                        if token in english_variants or eng_val in english_variants:
                            val_ar = str(getattr(si.item, "name_ar", "")).lower()
                            if arabic_key in val_ar or arabic_key in q_lower:
                                si.score += self.TRANSLITERATION_BOOST
                                si.details["transliteration"] = self.TRANSLITERATION_BOOST
                                break

            # 3. Fuzzy match for common misspellings
            for misspell, correct in self.MISSPELLING_MAP.items():
                if misspell in q_lower or q_lower in misspell:
                    for field in self.arabic_fields + self.english_fields:
                        val = str(getattr(si.item, field, "")).lower()
                        if correct in val:
                            si.score += self.FUZZY_BOOST
                            si.details["fuzzy_match"] = self.FUZZY_BOOST
                            break

            # 4. City/Region boost for local businesses
            city = str(getattr(si.item, "city", "")).strip()
            region = str(getattr(si.item, "region", "")).strip()
            city_lower = city.lower()
            region_lower = region.lower()

            if city and (city_lower in q_lower or q_lower in city_lower):
                si.score += self.CITY_BOOST
                si.details["city_match"] = self.CITY_BOOST
            if region and (region_lower in q_lower or q_lower in region_lower):
                si.score += self.REGION_BOOST
                si.details["region_match"] = self.REGION_BOOST

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
            ArabicNameMatchStage(),
            FreshnessStage(field="created_at"),
            TenantWeightStage(),
        ])
