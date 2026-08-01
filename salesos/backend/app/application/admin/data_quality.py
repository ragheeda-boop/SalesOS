"""Data Quality Dashboard — admin endpoints for monitoring data quality.

CI-19 Wave 2 Core (no sqlalchemy.text)

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
from datetime import UTC, datetime
from enum import Enum
from functools import reduce
from operator import add
from typing import Any, cast

from fastapi import APIRouter, Depends, Query
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    MetaData,
    String,
    Table,
    and_,
    case,
    func,
    literal,
    or_,
    select,
    union_all,
)
from sqlalchemy import (
    cast as sa_cast,
)
from sqlalchemy.dialects.postgresql import UUID

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Quality weight formula ─────────────────────────────────────────
COMPLETENESS_WEIGHT = 0.40
ACCURACY_WEIGHT = 0.30
FRESHNESS_WEIGHT = 0.30

# ── Core fields for quality evaluation ─────────────────────────────
CORE_FIELDS = [
    "name_ar",
    "name_en",
    "cr_number",
    "vat_number",
    "email",
    "phone",
    "website",
    "address",
    "city",
    "region",
    "industry",
    "status",
    "revenue",
    "employees",
]

_ALLOWED_QUALITY_FIELDS = frozenset(CORE_FIELDS)


_dq_metadata = MetaData()

# Lightweight Core table for quality SQL (columns referenced by quality checks).
companies = Table(
    "companies",
    _dq_metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True)),
    Column("name_ar", String),
    Column("name_en", String),
    Column("cr_number", String),
    Column("vat_number", String),
    Column("email", String),
    Column("phone", String),
    Column("website", String),
    Column("address", String),
    Column("city", String),
    Column("region", String),
    Column("industry", String),
    Column("status", String),
    Column("revenue", Float),
    Column("employees", String),
    Column("updated_at", DateTime(timezone=True)),
)


def _validate_quality_field(name: str) -> str:
    """Validate field name against allowlist to prevent SQL injection."""
    if name not in _ALLOWED_QUALITY_FIELDS:
        raise ValueError(f"Invalid quality field: {name}")
    return name


def _field_col(name: str):
    return companies.c[_validate_quality_field(name)]


def _apply_tenant(stmt, tenant_id: str | None):
    if tenant_id:
        return stmt.where(companies.c.tenant_id == tenant_id)
    return stmt


# ── Field freshness max valid hours ────────────────────────────────
FIELD_FRESHNESS_HOURS: dict[str, float] = {
    "name_ar": 8760,
    "name_en": 8760,
    "cr_number": 8760,
    "vat_number": 8760,
    "address": 4380,
    "phone": 4380,
    "email": 2160,
    "website": 4380,
    "revenue": 720,
    "employees": 720,
    "status": 720,
    "industry": 2160,
    "city": 8760,
    "region": 8760,
    "legal_form": 8760,
}

# ── Source reliability scores ──────────────────────────────────────
SOURCE_RELIABILITY: dict[str, float] = {
    "government": 0.95,
    "manual": 0.90,
    "erp": 0.85,
    "crm": 0.80,
    "linkedin": 0.70,
    "website": 0.60,
    "news": 0.50,
    "enrichment_api": 0.40,
    "ai_extraction": 0.30,
}


class FreshnessGrade(str, Enum):
    REAL_TIME = "real_time"  # < 1 hour
    FRESH = "fresh"  # < 24 hours
    MODERATE = "moderate"  # < 1 week
    STALE = "stale"  # < 30 days
    EXPIRED = "expired"  # > 30 days


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

    async def get_quality_summary(self, tenant_id: str | None = None) -> QualitySummary:
        """Compute overall quality score for the tenant."""
        if not self._session_factory:
            return self._summary_from_cache_or_default()

        cache_key = f"summary:{tenant_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cast(QualitySummary, cached)

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
            last_evaluated=datetime.now(UTC).isoformat(),
        )

        self._set_cache(cache_key, summary)
        return summary

    async def get_completeness(self, tenant_id: str | None = None) -> list[CompletenessStats]:
        """Get per-field completeness statistics."""
        if not self._session_factory:
            return []

        async with self._session_factory() as session:
            return await self._field_completeness(session, tenant_id)

    async def get_freshness(self, tenant_id: str | None = None) -> list[FreshnessStats]:
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
        filled_exprs = []
        for f in CORE_FIELDS:
            col = _field_col(f)
            filled_exprs.append(case((and_(col.is_not(None), col != ""), 1), else_=0))
        filled_sum = reduce(add, filled_exprs)
        total_fields = len(CORE_FIELDS)
        stmt = select(func.avg(sa_cast(filled_sum, Float) / total_fields)).select_from(companies)
        stmt = _apply_tenant(stmt, tenant_id)
        result = await session.execute(stmt)
        row = result.first()
        return float(row[0]) if row and row[0] is not None else 0.0

    async def _calc_accuracy(self, session: Any, tenant_id: str | None) -> float:
        """Calculate accuracy score based on source reliability and field validation."""
        stmt = select(
            func.avg(case((companies.c.email.like("%@%.%"), 0.15), else_=0)),
            func.avg(
                case(
                    (
                        and_(
                            companies.c.phone.is_not(None),
                            func.length(companies.c.phone) >= 7,
                        ),
                        0.10,
                    ),
                    else_=0,
                )
            ),
            func.avg(case((companies.c.website.like("%.%"), 0.10), else_=0)),
            func.avg(
                case(
                    (
                        and_(
                            companies.c.cr_number.is_not(None),
                            func.length(companies.c.cr_number) >= 5,
                        ),
                        0.15,
                    ),
                    else_=0,
                )
            ),
            func.count(),
        ).select_from(companies)
        stmt = _apply_tenant(stmt, tenant_id)
        result = await session.execute(stmt)
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
        now = func.now()
        freshness = case(
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 1), 1.0),
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 7), 0.9),
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 30), 0.6),
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 90), 0.3),
            else_=0.1,
        )
        stmt = select(func.avg(freshness), func.count()).select_from(companies)
        stmt = _apply_tenant(stmt, tenant_id)
        result = await session.execute(stmt)
        row = result.first()
        if not row or not row[1]:
            return 0.0

        return float(row[0]) if row[0] is not None else 0.0

    async def _count_records(self, session: Any, tenant_id: str | None) -> int:
        stmt = select(func.count()).select_from(companies)
        stmt = _apply_tenant(stmt, tenant_id)
        result = await session.execute(stmt)
        row = result.first()
        return int(row[0]) if row else 0

    async def _count_issues(self, session: Any, tenant_id: str | None) -> int:
        """Count records with quality issues (missing critical fields or stale data)."""
        issue_pred = or_(
            companies.c.name_ar.is_(None),
            companies.c.name_ar == "",
            companies.c.cr_number.is_(None),
            companies.c.cr_number == "",
            companies.c.updated_at < func.now() - func.make_interval(0, 0, 0, 90),
        )
        stmt = select(func.count()).select_from(companies).where(issue_pred)
        stmt = _apply_tenant(stmt, tenant_id)
        result = await session.execute(stmt)
        row = result.first()
        return int(row[0]) if row else 0

    async def _count_duplicates(self, session: Any, tenant_id: str | None) -> int:
        """Count potential duplicates (same CR number)."""
        inner = (
            select(companies.c.cr_number)
            .where(
                and_(
                    companies.c.cr_number.is_not(None),
                    companies.c.cr_number != "",
                )
            )
            .group_by(companies.c.cr_number)
            .having(func.count() > 1)
        )
        if tenant_id:
            inner = inner.where(companies.c.tenant_id == tenant_id)
        stmt = select(func.count()).select_from(inner.subquery("dups"))
        result = await session.execute(stmt)
        row = result.first()
        return int(row[0]) if row else 0

    async def _field_completeness(
        self, session: Any, tenant_id: str | None
    ) -> list[CompletenessStats]:
        """Per-field completeness breakdown."""
        parts = []
        for f in CORE_FIELDS:
            col = _field_col(f)
            part = select(
                literal(f).label("field_name"),
                func.sum(case((and_(col.is_not(None), col != ""), 1), else_=0)).label("filled"),
                func.count().label("total"),
            ).select_from(companies)
            part = _apply_tenant(part, tenant_id)
            parts.append(part)

        stmt = union_all(*parts)
        result = await session.execute(stmt)

        stats = []
        for row in result:
            filled = int(row[1])
            total = int(row[2])
            stats.append(
                CompletenessStats(
                    field_name=str(row[0]),
                    filled_count=filled,
                    total_count=total,
                    completeness_pct=round(filled / max(total, 1) * 100, 1),
                    null_count=total - filled,
                )
            )

        return stats

    async def _freshness_distribution(
        self, session: Any, tenant_id: str | None
    ) -> list[FreshnessStats]:
        """Freshness grade distribution."""
        now = func.now()
        grade = case(
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 0, 1), "real_time"),
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 1), "fresh"),
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 7), "moderate"),
            (companies.c.updated_at >= now - func.make_interval(0, 0, 0, 30), "stale"),
            else_="expired",
        ).label("grade")
        age_hours = (func.extract("epoch", now - companies.c.updated_at) / 3600).label("age_hours")

        sub = select(grade, age_hours).select_from(companies)
        sub = _apply_tenant(sub, tenant_id).subquery("sub")

        grade_order = case(
            (sub.c.grade == "real_time", 1),
            (sub.c.grade == "fresh", 2),
            (sub.c.grade == "moderate", 3),
            (sub.c.grade == "stale", 4),
            (sub.c.grade == "expired", 5),
            else_=6,
        )
        stmt = (
            select(
                sub.c.grade,
                func.count().label("cnt"),
                func.avg(sub.c.age_hours).label("avg_age"),
            )
            .group_by(sub.c.grade)
            .order_by(grade_order)
        )

        result = await session.execute(stmt)
        total_count = await self._count_records(session, tenant_id)

        stats = []
        for row in result:
            count = int(row[1])
            stats.append(
                FreshnessStats(
                    grade=str(row[0]),
                    count=count,
                    percentage=round(count / max(total_count, 1) * 100, 1),
                    avg_age_hours=round(float(row[2] or 0), 1),
                )
            )

        return stats

    async def _find_duplicates(
        self, session: Any, tenant_id: str | None, limit: int
    ) -> list[DuplicateCandidate]:
        """Find potential duplicate records by CR number."""
        c1 = companies.alias("c1")
        c2 = companies.alias("c2")
        sim = func.similarity(c1.c.name_ar, c2.c.name_ar)
        sim_score = case(
            (c1.c.name_ar == c2.c.name_ar, 1.0),
            (sim > 0.6, sim),
            else_=0.5,
        ).label("sim_score")

        stmt = (
            select(
                sa_cast(c1.c.id, String).label("id_a"),
                sa_cast(c2.c.id, String).label("id_b"),
                c1.c.name_ar.label("name_a"),
                c2.c.name_ar.label("name_b"),
                c1.c.cr_number,
                sim_score,
            )
            .select_from(
                c1.join(
                    c2,
                    and_(c1.c.cr_number == c2.c.cr_number, c1.c.id < c2.c.id),
                )
            )
            .where(
                and_(
                    c1.c.cr_number.is_not(None),
                    c1.c.cr_number != "",
                )
            )
            .order_by(sim_score.desc())
            .limit(limit)
        )
        if tenant_id:
            stmt = stmt.where(c1.c.tenant_id == tenant_id)

        result = await session.execute(stmt)
        duplicates = []

        for row in result:
            sim_v = float(row[5]) if row[5] else 0.5
            reasons = []
            if sim_v > 0.9:
                reasons.append("same_cr_number_and_name")
            elif sim_v > 0.7:
                reasons.append("same_cr_number_similar_name")
            else:
                reasons.append("same_cr_number_different_name")

            action = "auto_merge" if sim_v > 0.95 else "review" if sim_v > 0.7 else "keep_separate"

            duplicates.append(
                DuplicateCandidate(
                    id_a=str(row[0]),
                    id_b=str(row[1]),
                    name_a=str(row[2] or ""),
                    name_b=str(row[3] or ""),
                    cr_number=str(row[4] or ""),
                    similarity_score=round(sim_v, 2),
                    match_reasons=reasons,
                    recommended_action=action,
                )
            )

        return duplicates

    def _get_cache(self, key: str) -> Any:
        entry = self._cache.get(key)
        if entry:
            ts, value = entry
            if (datetime.now(UTC) - ts).total_seconds() < self._cache_ttl_seconds:
                return value
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = (datetime.now(UTC), value)

    def _summary_from_cache_or_default(self) -> QualitySummary:
        return QualitySummary(
            overall_score=0.0,
            completeness_score=0.0,
            accuracy_score=0.0,
            freshness_score=0.0,
            total_records=0,
            last_evaluated=datetime.now(UTC).isoformat(),
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
