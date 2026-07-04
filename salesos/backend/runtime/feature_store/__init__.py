"""Feature Store — precomputed business features with caching, event refresh, and provenance."""

from __future__ import annotations

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
    ):
        self._session_factory = session_factory
        self._event_runtime = event_runtime
        self._computers = {c.name: c for c in computers}
        self._logger = logger
        self.metrics = FeatureStoreMetrics()

    async def get_feature(
        self, company_id: str, tenant_id: str, feature_name: str
    ) -> Optional[FeatureResult]:
        """Return cached feature if fresh, otherwise compute."""
        async with self._session_factory() as session:
            row = await self._load_cached(session, company_id, tenant_id, feature_name)
            if row is not None:
                self.metrics.cache_hits += 1
                return FeatureResult(
                    score=row.score,
                    version=row.version,
                    computed_at=row.computed_at,
                    confidence=row.confidence,
                    contributing_signals=row.signals or {},
                    explanation=row.explanation or "",
                )
            computer = self._computers.get(feature_name)
            if not computer:
                return None
            company = await self._load_company(session, tenant_id, company_id)
            result = await self._compute_and_store(session, computer, company, tenant_id, company_id)
            return result

    async def get_features(
        self, company_id: str, tenant_id: str, feature_names: Optional[list[str]] = None
    ) -> dict[str, FeatureResult]:
        """Return multiple features for a company."""
        names = feature_names or list(self._computers.keys())
        results: dict[str, FeatureResult] = {}
        async with self._session_factory() as session:
            company = await self._load_company(session, tenant_id, company_id)
            for name in names:
                row = await self._load_cached(session, company_id, tenant_id, name)
                if row is not None:
                    self.metrics.cache_hits += 1
                    results[name] = FeatureResult(
                        score=row.score,
                        version=row.version,
                        computed_at=row.computed_at,
                        confidence=row.confidence,
                        contributing_signals=row.signals or {},
                        explanation=row.explanation or "",
                    )
                    continue
                computer = self._computers.get(name)
                if not computer:
                    continue
                result = await self._compute_and_store(session, computer, company, tenant_id, company_id)
                results[name] = result
        return results

    async def recompute(self, company_id: str, tenant_id: str) -> dict[str, FeatureResult]:
        """Force recompute ALL features for a company."""
        results: dict[str, FeatureResult] = {}
        async with self._session_factory() as session:
            company = await self._load_company(session, tenant_id, company_id)
            for name, computer in self._computers.items():
                result = await self._compute_and_store(session, computer, company, tenant_id, company_id)
                results[name] = result
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
