"""Data Quality Dashboard — admin endpoints for monitoring data quality.

Provides REST API endpoints for:
- Overall quality score (completeness 40% + accuracy 30% + freshness 30%)
- Field completeness statistics
- Data freshness distribution
- Duplicate detection
- Quality trend tracking

Usage:
    from app.application.admin.data_quality import DataQualityRouter
    app.include_router(DataQualityRouter, prefix="/api/v1/admin/data-quality", tags=["admin"])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Quality weight formula ─────────────────────────────────────────
COMPLETENESS_WEIGHT = 0.40
ACCURACY_WEIGHT = 0.30
FRESHNESS_WEIGHT = 0.30

# ── Core fields for quality evaluation ─────────────────────────────
CORE_FIELDS = [
    "name_ar", "name_en", "cr_number", "vat_number", "email",
    "phone", "website", "address", "city", "region",
    "industry", "status", "revenue", "employees",
]

_ALLOWED_QUALITY_FIELDS = frozenset(CORE_FIELDS)


def _validate_quality_field(name: str) -> str:
    """Validate field name against allowlist to prevent SQL injection."""
    if name not in _ALLOWED_QUALITY_FIELDS:
        raise ValueError(f"Invalid quality field: {name}")
    return name

# ── Field freshness max valid hours ────────────────────────────────
FIELD_FRESHNESS_HOURS: dict[str, float] = {
    "name_ar": 8760, "name_en": 8760, "cr_number": 8760,
    "vat_number": 8760, "address": 4380, "phone": 4380,
    "email": 2160, "website": 4380, "revenue": 720,
    "employees": 720, "status": 720, "industry": 2160,
    "city": 8760, "region": 8760, "legal_form": 8760,
}

# ── Source reliability scores ──────────────────────────────────────
SOURCE_RELIABILITY: dict[str, float] = {
    "government": 0.95, "manual": 0.90, "erp": 0.85,
    "crm": 0.80, "linkedin": 0.70, "website": 0.60,
    "news": 0.50, "enrichment_api": 0.40, "ai_extraction": 0.30,
}


class FreshnessGrade(str, Enum):
    REAL_TIME = "real_time"    # < 1 hour
    FRESH = "fresh"            # < 24 hours
    MODERATE = "moderate"      # < 1 week
    STALE = "stale"            # < 30 days
    EXPIRED = "expired"        # > 30 days


@dataclass
class CompletenessStats:
    """Per-field completeness statistics."""
    field_name: str
    filled_count: int = 0
    total_count: int = 0
    completeness_pct: float = 0.0
    null_count: int = 0
    sample_values: list[str] = field(default_factory=list)


@dataclass
class FreshnessStats:
    """Freshness distribution statistics."""
    grade: str = ""
    count: int = 0
    percentage: float = 0.0
    avg_age_hours: float = 0.0


@dataclass
class DuplicateCandidate:
    """Potential duplicate record."""
    id_a: str = ""
    id_b: str = ""
    name_a: str = ""
    name_b: str = ""
    cr_number: str = ""
    similarity_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)
    recommended_action: str = "review"


@dataclass
class QualitySummary:
    """Overall quality summary."""
    overall_score: float = 0.0
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    freshness_score: float = 0.0
    total_records: int = 0
    records_with_issues: int = 0
    duplicate_count: int = 0
    last_evaluated: str = ""


class DataQualityService:
    """Service for evaluating data quality across the company database.

    Provides:
    - Completeness analysis per field
    - Freshness grading per record
    - Accuracy scoring per record
    - Duplicate detection via CR number + name similarity
    - Composite quality score: 40% completeness + 30% accuracy + 30% freshness
    """

    def __init__(self, db_session_factory=None):
        self._session_factory = db_session_factory
        self._cache: dict[str, Any] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

    async def get_quality_summary(
        self, tenant_id: str | None = None
    ) -> QualitySummary:
        """Compute overall quality score for the tenant."""
        if not self._session_factory:
            return self._summary_from_cache_or_default()

        cache_key = f"summary:{tenant_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        async with self._session_factory() as session:
            completeness = await self._calc_completeness(session, tenant_id)
            accuracy = await self._calc_accuracy(session, tenant_id)
            freshness = await self._calc_freshness(session, tenant_id)
            total = await self._count_records(session, tenant_id)
            issues = await self._count_issues(session, tenant_id)
            duplicates = await self._count_duplicates(session, tenant_id)

        overall = (
            completeness * COMPLETENESS_WEIGHT
            + accuracy * ACCURACY_WEIGHT
            + freshness * FRESHNESS_WEIGHT
        )

        summary = QualitySummary(
            overall_score=round(overall, 2),
            completeness_score=round(completeness, 2),
            accuracy_score=round(accuracy, 2),
            freshness_score=round(freshness, 2),
            total_records=total,
            records_with_issues=issues,
            duplicate_count=duplicates,
            last_evaluated=datetime.now(timezone.utc).isoformat(),
        )

        self._set_cache(cache_key, summary)
        return summary

    async def get_completeness(
        self, tenant_id: str | None = None
    ) -> list[CompletenessStats]:
        """Get per-field completeness statistics."""
        if not self._session_factory:
            return []

        async with self._session_factory() as session:
            return await self._field_completeness(session, tenant_id)

    async def get_freshness(
        self, tenant_id: str | None = None
    ) -> list[FreshnessStats]:
        """Get data freshness distribution."""
        if not self._session_factory:
            return []

        async with self._session_factory() as session:
            return await self._freshness_distribution(session, tenant_id)

    async def get_duplicates(
        self, tenant_id: str | None = None, limit: int = 50
    ) -> list[DuplicateCandidate]:
        """Find potential duplicate records."""
        if not self._session_factory:
            return []

        async with self._session_factory() as session:
            return await self._find_duplicates(session, tenant_id, limit)

    # ── Internal calculation methods ──────────────────────────────────

    async def _calc_completeness(self, session: Any, tenant_id: str | None) -> float:
        """Calculate average completeness across all records."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        filled_conditions = []
        for f in CORE_FIELDS:
            _validate_quality_field(f)
            filled_conditions.append(f"(CASE WHEN c.{f} IS NOT NULL AND c.{f} != '' THEN 1 ELSE 0 END)")

        filled_sum = " + ".join(filled_conditions)
        total_fields = len(CORE_FIELDS)

        sql = sa_text(f"""
            SELECT AVG(({filled_sum})::float / {total_fields}) as avg_completeness
            FROM companies c {tenant_filter}
        """)

        result = await session.execute(sql, params)
        row = result.first()
        return float(row[0]) if row and row[0] is not None else 0.0

    async def _calc_accuracy(self, session: Any, tenant_id: str | None) -> float:
        """Calculate accuracy score based on source reliability and field validation."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        sql = sa_text(f"""
            SELECT
                AVG(CASE WHEN c.email LIKE '%@%.%' THEN 0.15 ELSE 0 END) as email_valid,
                AVG(CASE WHEN c.phone IS NOT NULL AND length(c.phone) >= 7 THEN 0.10 ELSE 0 END) as phone_valid,
                AVG(CASE WHEN c.website LIKE '%.%' THEN 0.10 ELSE 0 END) as website_valid,
                AVG(CASE WHEN c.cr_number IS NOT NULL AND length(c.cr_number) >= 5 THEN 0.15 ELSE 0 END) as cr_valid,
                COUNT(*) as total
            FROM companies c {tenant_filter}
        """)

        result = await session.execute(sql, params)
        row = result.first()
        if not row or not row[4]:
            return 0.0

        base = 0.5  # Base accuracy assuming good source mix
        email_bonus = float(row[0] or 0)
        phone_bonus = float(row[1] or 0)
        website_bonus = float(row[2] or 0)
        cr_bonus = float(row[3] or 0)

        return min(base + email_bonus + phone_bonus + website_bonus + cr_bonus, 1.0)

    async def _calc_freshness(self, session: Any, tenant_id: str | None) -> float:
        """Calculate freshness score based on update recency."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        sql = sa_text(f"""
            SELECT
                AVG(CASE
                    WHEN c.updated_at >= NOW() - INTERVAL '1 day' THEN 1.0
                    WHEN c.updated_at >= NOW() - INTERVAL '7 days' THEN 0.9
                    WHEN c.updated_at >= NOW() - INTERVAL '30 days' THEN 0.6
                    WHEN c.updated_at >= NOW() - INTERVAL '90 days' THEN 0.3
                    ELSE 0.1
                END) as avg_freshness,
                COUNT(*) as total
            FROM companies c {tenant_filter}
        """)

        result = await session.execute(sql, params)
        row = result.first()
        if not row or not row[1]:
            return 0.0

        return float(row[0]) if row[0] is not None else 0.0

    async def _count_records(self, session: Any, tenant_id: str | None) -> int:
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        sql = sa_text(f"SELECT COUNT(*) FROM companies c {tenant_filter}")
        result = await session.execute(sql, params)
        row = result.first()
        return int(row[0]) if row else 0

    async def _count_issues(self, session: Any, tenant_id: str | None) -> int:
        """Count records with quality issues (missing critical fields or stale data)."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        sql = sa_text(f"""
            SELECT COUNT(*) FROM companies c {tenant_filter}
            {'AND' if tenant_filter else 'WHERE'} (
                c.name_ar IS NULL OR c.name_ar = ''
                OR c.cr_number IS NULL OR c.cr_number = ''
                OR c.updated_at < NOW() - INTERVAL '90 days'
            )
        """)
        result = await session.execute(sql, params)
        row = result.first()
        return int(row[0]) if row else 0

    async def _count_duplicates(self, session: Any, tenant_id: str | None) -> int:
        """Count potential duplicates (same CR number)."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        sql = sa_text(f"""
            SELECT COUNT(*) FROM (
                SELECT cr_number
                FROM companies c {tenant_filter}
                WHERE cr_number IS NOT NULL AND cr_number != ''
                GROUP BY cr_number
                HAVING COUNT(*) > 1
            ) dups
        """)
        result = await session.execute(sql, params)
        row = result.first()
        return int(row[0]) if row else 0

    async def _field_completeness(
        self, session: Any, tenant_id: str | None
    ) -> list[CompletenessStats]:
        """Per-field completeness breakdown."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        field_conditions = []
        for f in CORE_FIELDS:
            _validate_quality_field(f)
            field_conditions.append(f"""
                SELECT '{f}' as field_name,
                       SUM(CASE WHEN c.{f} IS NOT NULL AND c.{f} != '' THEN 1 ELSE 0 END) as filled,
                       COUNT(*) as total
                FROM companies c {tenant_filter}
            """)

        combined_sql = " UNION ALL ".join(field_conditions)
        result = await session.execute(sa_text(combined_sql), params)

        stats = []
        for row in result:
            filled = int(row[1])
            total = int(row[2])
            stats.append(CompletenessStats(
                field_name=str(row[0]),
                filled_count=filled,
                total_count=total,
                completeness_pct=round(filled / max(total, 1) * 100, 1),
                null_count=total - filled,
            ))

        return stats

    async def _freshness_distribution(
        self, session: Any, tenant_id: str | None
    ) -> list[FreshnessStats]:
        """Freshness grade distribution."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params = {"tid": tenant_id} if tenant_id else {}

        sql = sa_text(f"""
            SELECT grade, COUNT(*) as cnt, AVG(age_hours) as avg_age FROM (
                SELECT CASE
                    WHEN c.updated_at >= NOW() - INTERVAL '1 hour' THEN 'real_time'
                    WHEN c.updated_at >= NOW() - INTERVAL '1 day' THEN 'fresh'
                    WHEN c.updated_at >= NOW() - INTERVAL '7 days' THEN 'moderate'
                    WHEN c.updated_at >= NOW() - INTERVAL '30 days' THEN 'stale'
                    ELSE 'expired'
                END as grade,
                EXTRACT(EPOCH FROM (NOW() - c.updated_at)) / 3600 as age_hours
                FROM companies c {tenant_filter}
            ) sub
            GROUP BY grade
            ORDER BY CASE grade
                WHEN 'real_time' THEN 1
                WHEN 'fresh' THEN 2
                WHEN 'moderate' THEN 3
                WHEN 'stale' THEN 4
                WHEN 'expired' THEN 5
            END
        """)

        result = await session.execute(sql, params)
        total_count = await self._count_records(session, tenant_id)

        stats = []
        for row in result:
            count = int(row[1])
            stats.append(FreshnessStats(
                grade=str(row[0]),
                count=count,
                percentage=round(count / max(total_count, 1) * 100, 1),
                avg_age_hours=round(float(row[2] or 0), 1),
            ))

        return stats

    async def _find_duplicates(
        self, session: Any, tenant_id: str | None, limit: int
    ) -> list[DuplicateCandidate]:
        """Find potential duplicate records by CR number."""
        from sqlalchemy import text as sa_text

        tenant_filter = "WHERE c.tenant_id = :tid" if tenant_id else ""
        params: dict[str, Any] = {"tid": tenant_id, "lim": limit} if tenant_id else {"lim": limit}

        sql = sa_text(f"""
            SELECT c1.id::text as id_a, c2.id::text as id_b,
                   c1.name_ar as name_a, c2.name_ar as name_b,
                   c1.cr_number,
                   CASE
                       WHEN c1.name_ar = c2.name_ar THEN 1.0
                       WHEN similarity(c1.name_ar, c2.name_ar) > 0.6
                       THEN similarity(c1.name_ar, c2.name_ar)
                       ELSE 0.5
                   END as sim_score
            FROM companies c1
            JOIN companies c2 ON c1.cr_number = c2.cr_number
                AND c1.id < c2.id
            {tenant_filter}
            {'AND' if tenant_filter else 'WHERE'} c1.cr_number IS NOT NULL
                AND c1.cr_number != ''
            ORDER BY sim_score DESC
            LIMIT :lim
        """)

        result = await session.execute(sql, params)
        duplicates = []

        for row in result:
            sim = float(row[5]) if row[5] else 0.5
            reasons = []
            if sim > 0.9:
                reasons.append("same_cr_number_and_name")
            elif sim > 0.7:
                reasons.append("same_cr_number_similar_name")
            else:
                reasons.append("same_cr_number_different_name")

            action = "auto_merge" if sim > 0.95 else "review" if sim > 0.7 else "keep_separate"

            duplicates.append(DuplicateCandidate(
                id_a=str(row[0]),
                id_b=str(row[1]),
                name_a=str(row[2] or ""),
                name_b=str(row[3] or ""),
                cr_number=str(row[4] or ""),
                similarity_score=round(sim, 2),
                match_reasons=reasons,
                recommended_action=action,
            ))

        return duplicates

    def _get_cache(self, key: str) -> Any:
        entry = self._cache.get(key)
        if entry:
            ts, value = entry
            if (datetime.now(timezone.utc) - ts).total_seconds() < self._cache_ttl_seconds:
                return value
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = (datetime.now(timezone.utc), value)

    def _summary_from_cache_or_default(self) -> QualitySummary:
        return QualitySummary(
            overall_score=0.0,
            completeness_score=0.0,
            accuracy_score=0.0,
            freshness_score=0.0,
            total_records=0,
            last_evaluated=datetime.now(timezone.utc).isoformat(),
        )


# ── Service singleton (initialized at app startup) ─────────────────
_quality_service: DataQualityService | None = None


def get_quality_service() -> DataQualityService:
    global _quality_service
    if _quality_service is None:
        _quality_service = DataQualityService()
    return _quality_service


def init_quality_service(session_factory) -> DataQualityService:
    global _quality_service
    _quality_service = DataQualityService(session_factory)
    return _quality_service


# ── API Endpoints ──────────────────────────────────────────────────

@router.get("/summary")
async def quality_summary(
    tenant_id: str | None = Query(None, description="Tenant UUID"),
    service: DataQualityService = Depends(get_quality_service),
):
    """GET /api/v1/admin/data-quality/summary — overall quality score.

    Quality formula: completeness (40%) + accuracy (30%) + freshness (30%)
    """
    return await service.get_quality_summary(tenant_id)


@router.get("/completeness")
async def field_completeness(
    tenant_id: str | None = Query(None, description="Tenant UUID"),
    service: DataQualityService = Depends(get_quality_service),
):
    """GET /api/v1/admin/data-quality/completeness — per-field completeness stats."""
    stats = await service.get_completeness(tenant_id)
    return {
        "fields": [
            {
                "field": s.field_name,
                "filled": s.filled_count,
                "total": s.total_count,
                "completeness_pct": s.completeness_pct,
                "null_count": s.null_count,
            }
            for s in stats
        ],
        "avg_completeness_pct": round(
            sum(s.completeness_pct for s in stats) / max(len(stats), 1), 1
        ),
    }


@router.get("/freshness")
async def data_freshness(
    tenant_id: str | None = Query(None, description="Tenant UUID"),
    service: DataQualityService = Depends(get_quality_service),
):
    """GET /api/v1/admin/data-quality/freshness — data age distribution."""
    stats = await service.get_freshness(tenant_id)
    return {
        "grades": [
            {
                "grade": s.grade,
                "count": s.count,
                "percentage": s.percentage,
                "avg_age_hours": s.avg_age_hours,
            }
            for s in stats
        ],
    }


@router.get("/duplicates")
async def duplicate_candidates(
    tenant_id: str | None = Query(None, description="Tenant UUID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    service: DataQualityService = Depends(get_quality_service),
):
    """GET /api/v1/admin/data-quality/duplicates — potential duplicate records."""
    dupes = await service.get_duplicates(tenant_id, limit)
    return {
        "duplicates": [
            {
                "id_a": d.id_a,
                "id_b": d.id_b,
                "name_a": d.name_a,
                "name_b": d.name_b,
                "cr_number": d.cr_number,
                "similarity_score": d.similarity_score,
                "match_reasons": d.match_reasons,
                "recommended_action": d.recommended_action,
            }
            for d in dupes
        ],
        "total_duplicates": len(dupes),
    }
