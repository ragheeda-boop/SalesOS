"""Tests for the Feature Store domain service — validates the full feature lifecycle."""

from __future__ import annotations

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from typing import Any

from ..models import EntityType, FeatureDefinition, FeatureType, FeatureValue
from ..repository import InMemoryFeatureStoreRepository
from ..service import FeatureStoreService


@pytest.fixture
def repo() -> InMemoryFeatureStoreRepository:
    return InMemoryFeatureStoreRepository()


@pytest.fixture
def service(repo: InMemoryFeatureStoreRepository) -> FeatureStoreService:
    return FeatureStoreService(repository=repo)


class TestFeatureDefinitions:
    """Register and retrieve feature definitions."""

    @pytest.mark.asyncio
    async def test_register_and_get_definition(self, service: FeatureStoreService):
        defn = FeatureDefinition(
            key="icp_score",
            name="ICP Score",
            description="Ideal Customer Profile alignment score",
            feature_type=FeatureType.NUMERIC,
            domain="scoring",
        )
        await service.register_feature(defn)
        result = await service.get_feature_definition("icp_score")

        assert result is not None
        assert result.key == "icp_score"
        assert result.name == "ICP Score"
        assert result.feature_type == FeatureType.NUMERIC
        assert result.domain == "scoring"

    @pytest.mark.asyncio
    async def test_register_multiple_definitions(self, service: FeatureStoreService):
        for key in ("icp_score", "funding_score", "hiring_score"):
            await service.register_feature(
                FeatureDefinition(key=key, name=key.replace("_", " ").title())
            )
        defs = await service.list_feature_definitions()
        assert len(defs) == 3

    @pytest.mark.asyncio
    async def test_list_definitions_by_domain(self, service: FeatureStoreService):
        await service.register_feature(FeatureDefinition(key="a", name="A", domain="scoring"))
        await service.register_feature(FeatureDefinition(key="b", name="B", domain="intent"))
        scoring = await service.list_feature_definitions(domain="scoring")
        assert len(scoring) == 1
        assert scoring[0].key == "a"

    @pytest.mark.asyncio
    async def test_get_nonexistent_definition(self, service: FeatureStoreService):
        result = await service.get_feature_definition("no_such_key")
        assert result is None


class TestFeatureValues:
    """Set and get feature values."""

    @pytest.mark.asyncio
    async def test_set_and_get_feature(self, service: FeatureStoreService):
        await service.set_feature("icp_score", "comp-1", "company", 85.5)
        val = await service.get_feature("icp_score", "comp-1", "company")

        assert val is not None
        assert val.feature_key == "icp_score"
        assert val.entity_id == "comp-1"
        assert val.value == 85.5
        assert val.entity_type == EntityType.COMPANY

    @pytest.mark.asyncio
    async def test_get_nonexistent_feature(self, service: FeatureStoreService):
        val = await service.get_feature("missing", "comp-1", "company")
        assert val is None

    @pytest.mark.asyncio
    async def test_delete_feature(self, service: FeatureStoreService):
        await service.set_feature("funding_score", "comp-1", "company", 90)
        deleted = await service.delete_feature("funding_score", "comp-1", "company")
        assert deleted is True

        val = await service.get_feature("funding_score", "comp-1", "company")
        assert val is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_feature(self, service: FeatureStoreService):
        deleted = await service.delete_feature("missing", "comp-1", "company")
        assert deleted is False


class TestBatchOperations:
    """Batch set features for an entity."""

    @pytest.mark.asyncio
    async def test_batch_set_features(self, service: FeatureStoreService):
        features = {
            "icp_score": 85.5,
            "funding_score": 90.0,
            "hiring_score": 72.3,
        }
        vals = await service.batch_set_features("comp-1", "company", features)

        assert len(vals) == 3
        keys = {v.feature_key for v in vals}
        assert keys == {"icp_score", "funding_score", "hiring_score"}

        # Verify individual retrieval
        val = await service.get_feature("icp_score", "comp-1", "company")
        assert val is not None
        assert val.value == 85.5

    @pytest.mark.asyncio
    async def test_get_features_with_filter(self, service: FeatureStoreService):
        await service.batch_set_features("comp-1", "company", {
            "icp_score": 85,
            "funding_score": 90,
        })
        vals = await service.get_features("comp-1", "company", feature_keys=["icp_score"])
        assert len(vals) == 1
        assert vals[0].feature_key == "icp_score"

    @pytest.mark.asyncio
    async def test_get_all_features_for_entity(self, service: FeatureStoreService):
        await service.batch_set_features("comp-1", "company", {"a": 1, "b": 2})
        await service.batch_set_features("comp-2", "company", {"a": 3})

        vals = await service.get_features("comp-1", "company")
        assert len(vals) == 2
        entity_ids = {v.entity_id for v in vals}
        assert entity_ids == {"comp-1"}


class TestEntitySnapshot:
    """Get full feature snapshot for scoring."""

    @pytest.mark.asyncio
    async def test_get_entity_snapshot(self, service: FeatureStoreService):
        await service.batch_set_features("comp-1", "company", {
            "icp_score": 85.5,
            "funding_score": 90.0,
            "hiring_score": 72.3,
            "growth_score": 68.0,
        })

        snapshot = await service.get_feature_snapshot("comp-1", "company")
        assert snapshot == {
            "icp_score": 85.5,
            "funding_score": 90.0,
            "hiring_score": 72.3,
            "growth_score": 68.0,
        }

    @pytest.mark.asyncio
    async def test_empty_snapshot(self, service: FeatureStoreService):
        snapshot = await service.get_feature_snapshot("comp-999", "company")
        assert snapshot == {}

    @pytest.mark.asyncio
    async def test_snapshot_across_entity_types(self, service: FeatureStoreService):
        await service.set_feature("score", "comp-1", "company", 80)
        await service.set_feature("score", "opp-1", "opportunity", 65)

        company_snap = await service.get_feature_snapshot("comp-1", "company")
        opp_snap = await service.get_feature_snapshot("opp-1", "opportunity")
        assert company_snap["score"] == 80
        assert opp_snap["score"] == 65


class TestTTLEXpiry:
    """TTL expiry removes stale features from reads."""

    @pytest.mark.asyncio
    async def test_expired_feature_not_returned(self, service: FeatureStoreService):
        await service.set_feature(
            "stale_feature", "comp-1", "company", 42, ttl_seconds=0
        )
        val = await service.get_feature("stale_feature", "comp-1", "company")
        assert val is None

    @pytest.mark.asyncio
    async def test_expired_feature_excluded_from_snapshot(self, service: FeatureStoreService):
        await service.set_feature("fresh", "comp-1", "company", 100, ttl_seconds=3600)
        await service.set_feature("stale", "comp-1", "company", 50, ttl_seconds=0)

        snapshot = await service.get_feature_snapshot("comp-1", "company")
        assert "fresh" in snapshot
        assert "stale" not in snapshot

    @pytest.mark.asyncio
    async def test_fresh_feature_returned(self, service: FeatureStoreService):
        await service.set_feature("ok", "comp-1", "company", 77, ttl_seconds=3600)
        val = await service.get_feature("ok", "comp-1", "company")
        assert val is not None
        assert val.value == 77


class TestComputeAndStore:
    """Compute-on-demand with caching."""

    @pytest.mark.asyncio
    async def test_compute_and_store(self, service: FeatureStoreService):
        call_count = 0

        async def compute_fn() -> int:
            nonlocal call_count
            call_count += 1
            return 42

        val = await service.compute_and_store(
            "computed", "comp-1", "company", compute_fn
        )
        assert val.value == 42
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_compute_and_store_uses_cache(self, service: FeatureStoreService):
        call_count = 0

        async def compute_fn() -> int:
            nonlocal call_count
            call_count += 1
            return 99

        await service.set_feature("cached", "comp-1", "company", 99, ttl_seconds=3600)
        val = await service.compute_and_store("cached", "comp-1", "company", compute_fn)
        assert val.value == 99
        assert call_count == 0  # compute_fn was NOT called

    @pytest.mark.asyncio
    async def test_compute_and_store_recomputes_when_expired(self, service: FeatureStoreService):
        call_count = 0

        async def compute_fn() -> int:
            nonlocal call_count
            call_count += 1
            return call_count * 10

        await service.set_feature("expire_me", "comp-1", "company", 10, ttl_seconds=0)
        val = await service.compute_and_store("expire_me", "comp-1", "company", compute_fn)
        assert val.value == 10  # compute_fn called once (set_feature does not call compute_fn)
        assert call_count == 1
