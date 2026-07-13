"""Search Strategy Matrix — maps search intent to executor strategy.

This is the central decision logic for which search backend handles which query.
It is NOT hardcoded in SearchPlanner. The Planner delegates to a StrategySelector
which returns the appropriate executor.

       Search Intent
            │
            ▼
    StrategySelector
            │
            ├── Exact CR Number  ────► PostgreSQL B-Tree (idx_companies_tenant_cr)
            ├── Exact Name       ────► PostgreSQL B-Tree (idx_companies_tenant_name_ar)
            ├── Partial Name     ────► Trigram GIN (idx_companies_name_ar_trgm)
            ├── Multi Filter     ────► PostgreSQL Composite Indexes
            ├── Arabic Full Text ────► TSVECTOR (future)
            ├── Semantic Search  ────► pgvector HNSW (future)
            ├── Similar Companies ───► pgvector HNSW (future)
            └── AI Copilot       ────► Hybrid (future)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class SearchIntent(Enum):
    """The intent behind a user's search query."""

    EXACT_CR = auto()
    EXACT_NAME = auto()
    EXACT_PHONE = auto()
    EXACT_EMAIL = auto()
    PARTIAL_NAME = auto()
    PARTIAL_CR = auto()
    PARTIAL_CITY = auto()
    PARTIAL_GENERAL = auto()
    MULTI_FILTER = auto()
    FULL_TEXT = auto()      # Arabic full-text (tsvector)
    SEMANTIC = auto()       # Natural language / meaning-based
    SIMILAR = auto()        # "Like this company"
    COPILOT = auto()        # AI agent / RAG


class SearchStrategy(Enum):
    """The execution strategy for a given intent."""

    POSTGRES_BTREE = "postgres_btree"
    POSTGRES_TRIGRAM = "postgres_trigram"
    POSTGRES_COMPOSITE = "postgres_composite"
    POSTGRES_TSVECTOR = "postgres_tsvector"
    PGVECTOR_HNSW = "pgvector_hnsw"
    HYBRID = "hybrid"


@dataclass
class IntentMatch:
    """Result of matching a query against known intents."""

    intent: SearchIntent
    strategy: SearchStrategy
    confidence: float  # 0.0 - 1.0
    reason: str = ""


# ─────────────────────────────────────────────
# Pattern matchers for each intent
# ─────────────────────────────────────────────

CR_PATTERN = re.compile(r"^\d{7,15}$")
PHONE_PATTERN = re.compile(r"^05\d{8}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CR_PREFIX_PATTERN = re.compile(r"^(cr|cr_number):", re.IGNORECASE)

# Terms that indicate semantic/natural language intent
SEMANTIC_INDICATORS = [
    "مثل", "similar", "like", "شبيه", "مشابه",
    "اقتراح", "recommend", "suggest",
    "أفضل", "best", "top",
]

# Legal prefixes to strip for normalization
LEGAL_PREFIXES = [
    "شركة", "شركه", "مؤسسة", "مؤسسه", "موسسه", "مجموعة", "مجموعه", "مصنع", "مكتب",
    "مستشفى", "مستشفي",
    "شركة ", "شركه ", "مؤسسة ", "مؤسسه ", "موسسه ", "مجموعة ", "مجموعه ",
]


def detect_intent(query: str, field_filters: dict[str, str] | None = None) -> IntentMatch:
    """Detect search intent from raw query and optional field filters.

    Returns the best-matching intent, strategy, and confidence score.
    """
    q = query.strip()
    ff = field_filters or {}

    # 1. Field-prefixed queries (cr:1234567890)
    if "cr" in ff or "cr_number" in ff:
        return IntentMatch(
            intent=SearchIntent.EXACT_CR,
            strategy=SearchStrategy.POSTGRES_BTREE,
            confidence=0.95,
            reason="Field prefix cr:/cr_number:",
        )

    # 2. Pure CR number
    if CR_PATTERN.match(q):
        return IntentMatch(
            intent=SearchIntent.EXACT_CR,
            strategy=SearchStrategy.POSTGRES_BTREE,
            confidence=0.90,
            reason="Numeric pattern matches CR number",
        )

    # 3. Phone number
    if PHONE_PATTERN.match(q):
        return IntentMatch(
            intent=SearchIntent.EXACT_PHONE,
            strategy=SearchStrategy.POSTGRES_BTREE,
            confidence=0.90,
            reason="Phone number pattern",
        )

    # 4. Email
    if EMAIL_PATTERN.match(q):
        return IntentMatch(
            intent=SearchIntent.EXACT_EMAIL,
            strategy=SearchStrategy.POSTGRES_BTREE,
            confidence=0.95,
            reason="Email pattern",
        )

    # 5. Multiple filters (status=, city=, etc.)
    if len(ff) >= 2 or any(len(v) > 0 for v in ff.values()):
        return IntentMatch(
            intent=SearchIntent.MULTI_FILTER,
            strategy=SearchStrategy.POSTGRES_COMPOSITE,
            confidence=0.85,
            reason=f"Multiple field filters: {ff}",
        )

    # 6. Semantic / natural language
    for indicator in SEMANTIC_INDICATORS:
        if indicator in q:
            return IntentMatch(
                intent=SearchIntent.SEMANTIC,
                strategy=SearchStrategy.PGVECTOR_HNSW,
                confidence=0.70,
                reason=f"Semantic indicator found: '{indicator}'",
            )

    # 7. Short general text → partial / trigram
    return IntentMatch(
        intent=SearchIntent.PARTIAL_GENERAL,
        strategy=SearchStrategy.POSTGRES_TRIGRAM,
        confidence=0.60,
        reason="Default: general partial search",
    )


def normalize_query(query: str) -> str:
    """Normalize query by stripping legal prefixes and Arabic variants for better matching.

    Uses ArabicSearchNormalizer for comprehensive normalization and
    legal prefix stripping for better trigram matching.

    "شركة الكهرباء" → "الكهرباء"
    "مؤسسة أحمد للتجارة" → "احمد للتجاره"
    "شَرِكَةُ المقاولات" → "المقاولات"
    """
    q = query.strip()
    # First normalize Arabic (diacritics, alef, yeh, teh marbuta)
    try:
        from ..normalization import ArabicSearchNormalizer
        normalizer = ArabicSearchNormalizer.default()
        q = normalizer.normalize(q)
    except ImportError:
        pass

    # Then strip legal prefixes
    for prefix in LEGAL_PREFIXES:
        if q.startswith(prefix):
            q = q[len(prefix):].strip()
            break
    return q


# ─────────────────────────────────────────────
# Reference Matrix (for documentation)
# ─────────────────────────────────────────────

STRATEGY_MATRIX: list[dict[str, Any]] = [
    {
        "intent": "EXACT_CR",
        "pattern": "رقم سجل تجاري كامل",
        "example": "1010123456",
        "strategy": "PostgreSQL B-Tree",
        "index": "idx_companies_tenant_cr",
        "p95_100k": "<1ms",
        "verified": True,
    },
    {
        "intent": "EXACT_NAME",
        "pattern": "اسم شركة كامل",
        "example": "شركة الأمل للتجارة",
        "strategy": "PostgreSQL B-Tree",
        "index": "idx_companies_tenant_name_ar",
        "p95_100k": "<1ms",
        "verified": True,
    },
    {
        "intent": "PARTIAL_NAME",
        "pattern": "جزء من الاسم (وسط)",
        "example": "%تجارة%",
        "strategy": "PostgreSQL Trigram (GIN)",
        "index": "idx_companies_name_ar_trgm",
        "p95_100k": "78ms",
        "verified": True,
    },
    {
        "intent": "PARTIAL_NAME_HIGH_SELECTIVITY",
        "pattern": "بادئة عالية الانتشار",
        "example": "شركة% (55% match)",
        "strategy": "PostgreSQL Seq Scan (Trigram less effective)",
        "index": "—",
        "p95_100k": "~500ms",
        "verified": True,
        "note": "High selectivity → needs Search Normalization or tsvector",
    },
    {
        "intent": "MULTI_FILTER",
        "pattern": "حقول متعددة",
        "example": "status + city + region",
        "strategy": "PostgreSQL Composite + Trigram",
        "index": "idx_companies_tenant_* + *_trgm",
        "p95_100k": "15-250ms",
        "verified": True,
    },
    {
        "intent": "SEMANTIC",
        "pattern": "بحث دلالي / لغة طبيعية",
        "example": "شركات مشابهة لهذه",
        "strategy": "pgvector (HNSW)",
        "index": "vector index",
        "p95_100k": "TBD — Phase 4",
        "verified": False,
    },
    {
        "intent": "FULL_TEXT",
        "pattern": "نص عربي كامل",
        "example": "مقاولات حكومية",
        "strategy": "PostgreSQL TSVECTOR",
        "index": "GIN tsvector",
        "p95_100k": "TBD — future",
        "verified": False,
    },
    {
        "intent": "SIMILAR",
        "pattern": "إيجاد شركات مشابهة",
        "example": "similar_to:company_id",
        "strategy": "pgvector (HNSW)",
        "index": "vector index",
        "p95_100k": "TBD — Phase 4",
        "verified": False,
    },
]
