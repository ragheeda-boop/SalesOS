"""Feature Store — precomputed business features with caching, event refresh, and provenance."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, registry

from runtime.event_runtime import EventRuntime

FeatureBase = declarative_base()


class CompanyFeatureModel(FeatureBase):
    __tablename__ = "company_features"
    __table_args__ = (
        UniqueConstraint("tenant_id", "company_id", "feature_name", name="uq_company_feature"),
        {"schema": "public"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False)
    company_id = Column(String(36), nullable=False)
    feature_name = Column(String(64), nullable=False)
    score = Column(Float, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    computed_at = Column(DateTime(timezone=True), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    signals = Column(JSON, nullable=True)
    explanation = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


@dataclass
class FeatureResult:
    score: float
    version: int
    computed_at: datetime
    confidence: float
    contributing_signals: dict[str, Any]
    explanation: str


class FeatureComputer:
    """Base class for a single feature computation."""

    name: str
    version: int = 1

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        raise NotImplementedError


@dataclass
class FeatureStoreMetrics:
    computations: int = 0
    cache_hits: int = 0
    total_compute_ms: float = 0.0
    errors: int = 0

    def snapshot(self) -> dict:
        return {
            "computations": self.computations,
            "cache_hits": self.cache_hits,
            "total_compute_ms": round(self.total_compute_ms, 2),
            "errors": self.errors,
            "avg_compute_ms": round(self.total_compute_ms / max(self.computations, 1), 2),
        }


FEATURE_CACHE_PREFIX = "feature"


def _build_feature_cache_key(tenant_id: str, company_id: str, feature_name: str) -> str:
    return f"{FEATURE_CACHE_PREFIX}:{tenant_id}:{company_id}:{feature_name}"


def _build_company_cache_pattern(tenant_id: str, company_id: str) -> str:
    return f"{FEATURE_CACHE_PREFIX}:{tenant_id}:{company_id}:*"


class FeatureStore:
    """Orchestrates feature computation, caching, and event-triggered refresh.

    Usage:
        store = FeatureStore(session_factory, event_runtime, [IcpComputer(), ...])
        await store.get_features(company_id=..., tenant_id=...)  # cached
        await store.recompute(company_id=..., tenant_id=...)     # force
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        event_runtime: EventRuntime,
        computers: list[FeatureComputer],
        logger: Any = None,
        cache_service: Any = None,
        cache_ttl: int = 300,
    ):
        self._session_factory = session_factory
        self._event_runtime = event_runtime
        self._computers = {c.name: c for c in computers}
        self._logger = logger
        self._cache_service = cache_service
        self._cache_ttl = cache_ttl
        self.metrics = FeatureStoreMetrics()

    async def get_feature(
        self, company_id: str, tenant_id: str, feature_name: str
    ) -> Optional[FeatureResult]:
        """Return cached feature if fresh, otherwise compute.

        Tries Redis cache first (if configured), falls back to DB-level cache,
        then computes on miss.
        """
        # 1. Try Redis cache
        cached = await self._redis_get_feature(company_id, tenant_id, feature_name)
        if cached is not None:
            return cached

        async with self._session_factory() as session:
            # 2. Try DB-level cache
            row = await self._load_cached(session, company_id, tenant_id, feature_name)
            if row is not None:
                self.metrics.cache_hits += 1
                result = FeatureResult(
                    score=row.score,
                    version=row.version,
                    computed_at=row.computed_at,
                    confidence=row.confidence,
                    contributing_signals=row.signals or {},
                    explanation=row.explanation or "",
                )
                await self._redis_set_feature(company_id, tenant_id, feature_name, result)
                return result
            computer = self._computers.get(feature_name)
            if not computer:
                return None
            company = await self._load_company(session, tenant_id, company_id)
            result = await self._compute_and_store(session, computer, company, tenant_id, company_id)
            await self._redis_set_feature(company_id, tenant_id, feature_name, result)
            return result

    async def get_features(
        self, company_id: str, tenant_id: str, feature_names: Optional[list[str]] = None
    ) -> dict[str, FeatureResult]:
        """Return multiple features for a company.

        Cached features load instantly; uncached features are computed in parallel.
        Tries Redis cache first (if configured), then DB-level cache, then compute.
        """
        names = feature_names or list(self._computers.keys())
        results: dict[str, FeatureResult] = {}
        needs_compute: list[str] = []

        # 1. Try Redis cache for each name
        for name in names:
            cached = await self._redis_get_feature(company_id, tenant_id, name)
            if cached is not None:
                results[name] = cached
            else:
                needs_compute.append(name)

        if not needs_compute:
            return results

        # 2. For Redis misses, try DB cache or compute
        async with self._session_factory() as session:
            company = await self._load_company(session, tenant_id, company_id)
            still_needs: list[str] = []

            for name in needs_compute:
                row = await self._load_cached(session, company_id, tenant_id, name)
                if row is not None:
                    self.metrics.cache_hits += 1
                    result = FeatureResult(
                        score=row.score,
                        version=row.version,
                        computed_at=row.computed_at,
                        confidence=row.confidence,
                        contributing_signals=row.signals or {},
                        explanation=row.explanation or "",
                    )
                    results[name] = result
                    await self._redis_set_feature(company_id, tenant_id, name, result)
                    continue
                computer = self._computers.get(name)
                if not computer:
                    continue
                still_needs.append(name)

            if still_needs:
                import asyncio
                async def _compute_one(feature_name: str):
                    computer = self._computers[feature_name]
                    fresult = await self._compute_and_store(
                        session, computer, company, tenant_id, company_id,
                    )
                    await self._redis_set_feature(company_id, tenant_id, feature_name, fresult)
                    return feature_name, fresult
                tasks = [_compute_one(n) for n in still_needs]
                computed = await asyncio.gather(*tasks, return_exceptions=True)
                for item in computed:
                    if isinstance(item, Exception):
                        continue
                    fname, fresult = item
                    results[fname] = fresult
        return results

    async def recompute(self, company_id: str, tenant_id: str) -> dict[str, FeatureResult]:
        """Force recompute ALL features for a company.

        All feature computers run in parallel since they are independent.
        Results are stored in a single bulk UPSERT with one commit
        instead of 7 individual SELECT → INSERT/UPDATE → COMMIT round-trips.
        """
        import asyncio
        from datetime import datetime, timezone

        results: dict[str, FeatureResult] = {}
        async with self._session_factory() as session:
            company = await self._load_company(session, tenant_id, company_id)

            async def _recompute_one(feature_name: str):
                computer = self._computers[feature_name]
                t0 = time.monotonic()
                try:
                    result = await computer.compute(company, session)
                    elapsed = (time.monotonic() - t0) * 1000
                    self.metrics.computations += 1
                    self.metrics.total_compute_ms += elapsed
                    return feature_name, result
                except Exception as exc:
                    elapsed = (time.monotonic() - t0) * 1000
                    self.metrics.errors += 1
                    if self._logger:
                        self._logger.error(
                            "Feature compute error: %s on %s/%s: %s",
                            computer.name, tenant_id, company_id, exc,
                        )
                    return feature_name, None

            tasks = [_recompute_one(n) for n in self._computers]
            computed = await asyncio.gather(*tasks, return_exceptions=True)

            # Bulk UPSERT — single round-trip, single commit
            now = datetime.now(timezone.utc)
            upsert_rows = []
            for item in computed:
                if isinstance(item, Exception):
                    continue
                fname, fresult = item
                if fresult is None:
                    continue
                results[fname] = fresult
                upsert_rows.append({
                    "p_tenant_id": tenant_id,
                    "p_company_id": company_id,
                    "p_feature_name": fname,
                    "p_score": fresult.score,
                    "p_version": fresult.version,
                    "p_computed_at": fresult.computed_at,
                    "p_confidence": fresult.confidence,
                    "p_signals": fresult.contributing_signals,
                    "p_explanation": fresult.explanation,
                    "p_now": now,
                })

            if upsert_rows:
                from sqlalchemy import text as sql_text
                await session.execute(
                    sql_text("""
                        INSERT INTO public.company_features
                            (tenant_id, company_id, feature_name, score, version,
                             computed_at, confidence, signals, explanation,
                             created_at, updated_at)
                        VALUES
                            (:p_tenant_id, :p_company_id, :p_feature_name, :p_score,
                             :p_version, :p_computed_at, :p_confidence,
                             CAST(:p_signals AS jsonb), :p_explanation,
                             :p_now, :p_now)
                        ON CONFLICT (tenant_id, company_id, feature_name)
                        DO UPDATE SET
                            score = EXCLUDED.score,
                            version = EXCLUDED.version,
                            computed_at = EXCLUDED.computed_at,
                            confidence = EXCLUDED.confidence,
                            signals = EXCLUDED.signals,
                            explanation = EXCLUDED.explanation,
                            updated_at = EXCLUDED.updated_at
                    """),
                    upsert_rows,
                )
                await session.commit()

        # Invalidate Redis cache for this company's features
        await self._redis_clear_company(tenant_id, company_id)
        return results

    async def _compute_and_store(
        self,
        session: AsyncSession,
        computer: FeatureComputer,
        company: dict[str, Any],
        tenant_id: str,
        company_id: str,
    ) -> FeatureResult:
        t0 = time.monotonic()
        try:
            result = await computer.compute(company, session)
            elapsed = (time.monotonic() - t0) * 1000
            self.metrics.computations += 1
            self.metrics.total_compute_ms += elapsed
            await self._store_result(session, tenant_id, company_id, computer.name, result)
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            self.metrics.errors += 1
            if self._logger:
                self._logger.error("Feature compute error: %s on %s/%s: %s", computer.name, tenant_id, company_id, exc)
            raise

    async def _load_company(self, session: AsyncSession, tenant_id: str, company_id: str) -> dict[str, Any]:
        from sqlalchemy import text
        row = await session.execute(
            text("SELECT * FROM public.companies WHERE tenant_id = :t AND id = :c"),
            {"t": tenant_id, "c": company_id},
        )
        r = row.mappings().one_or_none()
        if not r:
            return {"id": company_id, "tenant_id": tenant_id}
        return dict(r)

    async def _load_cached(
        self, session: AsyncSession, company_id: str, tenant_id: str, feature_name: str
    ) -> Optional[Any]:
        from sqlalchemy import select
        result = await session.execute(
            select(CompanyFeatureModel).where(
                CompanyFeatureModel.tenant_id == tenant_id,
                CompanyFeatureModel.company_id == company_id,
                CompanyFeatureModel.feature_name == feature_name,
            )
        )
        return result.scalar_one_or_none()

    # ── Redis cache helpers (optional, graceful failover) ──────────────

    async def _redis_get_feature(
        self, company_id: str, tenant_id: str, feature_name: str
    ) -> Optional[FeatureResult]:
        if self._cache_service is None:
            return None
        key = _build_feature_cache_key(tenant_id, company_id, feature_name)
        try:
            raw = await self._cache_service.get(key)
            if raw is None:
                return None
            self.metrics.cache_hits += 1
            return FeatureResult(
                score=raw["score"],
                version=raw["version"],
                computed_at=datetime.fromisoformat(raw["computed_at"]),
                confidence=raw["confidence"],
                contributing_signals=raw.get("contributing_signals", {}),
                explanation=raw.get("explanation", ""),
            )
        except Exception:
            return None

    async def _redis_set_feature(
        self, company_id: str, tenant_id: str, feature_name: str, result: FeatureResult
    ) -> None:
        if self._cache_service is None:
            return
        key = _build_feature_cache_key(tenant_id, company_id, feature_name)
        try:
            await self._cache_service.set(
                key,
                {
                    "score": result.score,
                    "version": result.version,
                    "computed_at": result.computed_at.isoformat(),
                    "confidence": result.confidence,
                    "contributing_signals": result.contributing_signals,
                    "explanation": result.explanation,
                },
                ttl_seconds=self._cache_ttl,
            )
        except Exception:
            pass

    async def _redis_clear_company(self, tenant_id: str, company_id: str) -> None:
        if self._cache_service is None:
            return
        if hasattr(self._cache_service, "scan_delete"):
            pattern = _build_company_cache_pattern(tenant_id, company_id)
            try:
                await self._cache_service.scan_delete(pattern)
            except Exception:
                pass
        else:
            try:
                await self._cache_service.delete_pattern(
                    _build_company_cache_pattern(tenant_id, company_id)
                )
            except Exception:
                pass

    async def _store_result(
        self,
        session: AsyncSession,
        tenant_id: str,
        company_id: str,
        feature_name: str,
        result: FeatureResult,
    ):
        from sqlalchemy import select, text
        row = await self._load_cached(session, company_id, tenant_id, feature_name)
        now = datetime.now(timezone.utc)
        if row:
            row.score = result.score
            row.version = result.version
            row.computed_at = result.computed_at
            row.confidence = result.confidence
            row.signals = result.contributing_signals
            row.explanation = result.explanation
            row.updated_at = now
        else:
            session.add(
                CompanyFeatureModel(
                    tenant_id=tenant_id,
                    company_id=company_id,
                    feature_name=feature_name,
                    score=result.score,
                    version=result.version,
                    computed_at=result.computed_at,
                    confidence=result.confidence,
                    signals=result.contributing_signals,
                    explanation=result.explanation,
                )
            )
        await session.commit()
