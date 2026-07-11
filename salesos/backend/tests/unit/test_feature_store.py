"""Tests for FeatureStore — orchestration, caching, metrics, recompute."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.feature_store import (
    FeatureStore,
    FeatureStoreMetrics,
    FeatureComputer,
    FeatureResult,
    CompanyFeatureModel,
)


# ── Fake SQLAlchemy helpers ──────────────────────────────────────────────────

class FakeMapping:
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]
    def get(self, key, default=None):
        return self._data.get(key, default)
    def keys(self):
        return self._data.keys()
    def __iter__(self):
        return iter(self._data)


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one
    def one(self):
        return FakeMapping(self._one) if self._one else None
    def one_or_none(self):
        return FakeMapping(self._one) if self._one else None
    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None, scalar_val=None):
        self._mappings = mappings_obj or FakeMappings()
        self._scalar_val = scalar_val
    def mappings(self):
        return self._mappings
    def scalar_one_or_none(self):
        return self._scalar_val
    def scalar(self):
        return self._scalar_val or 0


# ── Dummy Computer ───────────────────────────────────────────────────────────

class DummyComputer(FeatureComputer):
    name = "dummy_score"
    version = 1

    async def compute(self, company: dict, session: AsyncSession) -> FeatureResult:
        return FeatureResult(
            score=75.0,
            version=self.version,
            computed_at=datetime.now(timezone.utc),
            confidence=0.9,
            contributing_signals={"dummy": True},
            explanation="Dummy score",
        )


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_session():
    """Returns a session that returns no cached results, simulating a cache miss."""
    async def execute(sql_str, params=None):
        text = str(sql_str)
        if "SELECT" in text and "company_features" in text:
            return FakeResult(scalar_val=None)
        if "SELECT * FROM public.companies" in text:
            return FakeResult(FakeMappings(one={"id": "co-1", "tenant_id": "t-1", "name": "Test Co"}))
        return FakeResult()
    session = AsyncMock(spec=AsyncSession)
    session.execute = execute
    return session


@pytest.fixture
def mock_session_factory(mock_session):
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = mock_session
    factory.return_value.__aexit__.return_value = None
    return factory


@pytest.fixture
def event_runtime():
    return MagicMock()


@pytest.fixture
def feature_store(mock_session_factory, event_runtime):
    return FeatureStore(
        session_factory=mock_session_factory,
        event_runtime=event_runtime,
        computers=[DummyComputer()],
    )


# ── Tests: FeatureStoreMetrics ───────────────────────────────────────────────

class TestFeatureStoreMetrics:
    def test_snapshot_returns_dict(self):
        metrics = FeatureStoreMetrics()
        snap = metrics.snapshot()
        assert isinstance(snap, dict)
        assert "computations" in snap
        assert "cache_hits" in snap
        assert "total_compute_ms" in snap
        assert "errors" in snap

    def test_snapshot_avg_compute_ms(self):
        metrics = FeatureStoreMetrics()
        metrics.computations = 10
        metrics.total_compute_ms = 500.0
        snap = metrics.snapshot()
        assert snap["avg_compute_ms"] == 50.0

    def test_snapshot_zero_computations(self):
        metrics = FeatureStoreMetrics()
        snap = metrics.snapshot()
        assert snap["avg_compute_ms"] == 0.0

    def test_increments_computations(self):
        metrics = FeatureStoreMetrics()
        metrics.computations += 1
        assert metrics.computations == 1

    def test_increments_cache_hits(self):
        metrics = FeatureStoreMetrics()
        metrics.cache_hits += 1
        assert metrics.cache_hits == 1


# ── Tests: FeatureStore.get_feature ──────────────────────────────────────────

class TestGetFeature:
    async def test_returns_feature_result(self, feature_store):
        result = await feature_store.get_feature("co-1", "t-1", "dummy_score")
        assert isinstance(result, FeatureResult)
        assert result.score == 75.0

    async def test_returns_none_for_unknown_computer(self, feature_store):
        result = await feature_store.get_feature("co-1", "t-1", "nonexistent")
        assert result is None

    async def test_increments_computations_on_miss(self, feature_store):
        before = feature_store.metrics.computations
        await feature_store.get_feature("co-1", "t-1", "dummy_score")
        assert feature_store.metrics.computations == before + 1

    async def test_increments_cache_hits_on_hit(self, mock_session_factory, event_runtime):
        # Create a session that returns cached result
        cached_model = MagicMock(spec=CompanyFeatureModel)
        cached_model.score = 80.0
        cached_model.version = 1
        cached_model.computed_at = datetime.now(timezone.utc)
        cached_model.confidence = 0.9
        cached_model.signals = {"cached": True}
        cached_model.explanation = "Cached result"

        async def execute(sql_str, params=None):
            text = str(sql_str)
            if "SELECT" in text and "company_features" in text:
                return FakeResult(scalar_val=cached_model)
            if "SELECT * FROM public.companies" in text:
                return FakeResult(FakeMappings(one={"id": "co-1", "tenant_id": "t-1"}))
            return FakeResult()

        session = AsyncMock(spec=AsyncSession)
        session.execute = execute
        factory = MagicMock()
        factory.return_value.__aenter__.return_value = session
        factory.return_value.__aexit__.return_value = None

        store = FeatureStore(session_factory=factory, event_runtime=event_runtime, computers=[DummyComputer()])
        before_hits = store.metrics.cache_hits
        result = await store.get_feature("co-1", "t-1", "dummy_score")
        assert result.score == 80.0
        assert store.metrics.cache_hits == before_hits + 1


# ── Tests: FeatureStore.get_features ─────────────────────────────────────────

class TestGetFeatures:
    async def test_returns_dict(self, feature_store):
        results = await feature_store.get_features("co-1", "t-1")
        assert isinstance(results, dict)
        assert "dummy_score" in results

    async def test_returns_multiple_features(self, feature_store):
        results = await feature_store.get_features("co-1", "t-1", ["dummy_score"])
        assert len(results) == 1

    async def test_skips_unknown_features(self, feature_store):
        results = await feature_store.get_features("co-1", "t-1", ["dummy_score", "nonexistent"])
        assert len(results) == 1
        assert "dummy_score" in results

    async def test_returns_all_when_no_names_given(self, feature_store):
        results = await feature_store.get_features("co-1", "t-1")
        assert len(results) == 1  # Only dummy_score is registered


# ── Tests: FeatureStore.recompute ────────────────────────────────────────────

class TestRecompute:
    async def test_recompute_returns_all_results(self, feature_store):
        results = await feature_store.recompute("co-1", "t-1")
        assert isinstance(results, dict)
        assert "dummy_score" in results

    async def test_recompute_increments_computations(self, feature_store):
        before = feature_store.metrics.computations
        await feature_store.recompute("co-1", "t-1")
        assert feature_store.metrics.computations == before + 1

    async def test_recompute_does_not_cache_hit(self, feature_store):
        before_hits = feature_store.metrics.cache_hits
        await feature_store.recompute("co-1", "t-1")
        assert feature_store.metrics.cache_hits == before_hits  # recompute bypasses cache


# ── Tests: FeatureComputer Base ──────────────────────────────────────────────

class TestFeatureComputerBase:
    async def test_compute_raises_not_implemented(self):
        computer = FeatureComputer()
        computer.name = "base"
        with pytest.raises(NotImplementedError):
            await computer.compute({}, AsyncMock())

    def test_default_version(self):
        computer = FeatureComputer()
        assert computer.version == 1


# ── Tests: error handling ────────────────────────────────────────────────────

class TestErrorHandling:
    async def test_computer_error_caught(self, mock_session_factory, event_runtime):
        class BrokenComputer(FeatureComputer):
            name = "broken"
            async def compute(self, company, session):
                raise ValueError("Broken!")

        store = FeatureStore(
            session_factory=mock_session_factory,
            event_runtime=event_runtime,
            computers=[BrokenComputer()],
        )
        with pytest.raises(ValueError, match="Broken!"):
            await store.get_feature("co-1", "t-1", "broken")

    async def test_error_increments_errors_metric(self, mock_session_factory, event_runtime):
        class FailingComputer(FeatureComputer):
            name = "failing"
            async def compute(self, company, session):
                raise RuntimeError("fail")

        store = FeatureStore(
            session_factory=mock_session_factory,
            event_runtime=event_runtime,
            computers=[FailingComputer()],
        )
        before_errors = store.metrics.errors
        with pytest.raises(RuntimeError):
            await store.get_feature("co-1", "t-1", "failing")
        assert store.metrics.errors == before_errors + 1
