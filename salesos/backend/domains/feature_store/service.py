from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .models import FeatureDefinition, FeatureType, FeatureValue, EntityType
from .repository import FeatureStoreRepository


class FeatureStoreService:
    """Domain service for the Feature Store.

    Provides a generic, entity-agnostic key-value feature store that feeds
    the ScoringEngine and Decision Platform.  Supports TTL-based cache
    expiry, batch operations, and compute-on-demand via caller-supplied
    functions.
    """

    def __init__(self, repository: FeatureStoreRepository):
        self._repo = repository

    # ── Definitions ──────────────────────────────────────────────

    async def register_feature(self, definition: FeatureDefinition) -> FeatureDefinition:
        return await self._repo.save_definition(definition)

    async def get_feature_definition(self, key: str) -> Optional[FeatureDefinition]:
        return await self._repo.get_definition(key)

    async def list_feature_definitions(self, domain: str | None = None) -> list[FeatureDefinition]:
        return await self._repo.list_definitions(domain)

    # ── Single feature operations ────────────────────────────────

    async def get_feature(
        self,
        feature_key: str,
        entity_id: str,
        entity_type: str,
    ) -> Optional[FeatureValue]:
        val = await self._repo.get_value(feature_key, entity_id, entity_type)
        if val is not None and val.is_expired:
            await self._repo.delete_value(feature_key, entity_id, entity_type)
            return None
        return val

    async def set_feature(
        self,
        feature_key: str,
        entity_id: str,
        entity_type: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> FeatureValue:
        fv = FeatureValue(
            feature_key=feature_key,
            entity_id=entity_id,
            entity_type=EntityType(entity_type),
            value=value,
            computed_at=datetime.now(timezone.utc),
            ttl_seconds=ttl_seconds,
        )
        return await self._repo.save_value(fv)

    async def delete_feature(
        self,
        feature_key: str,
        entity_id: str,
        entity_type: str,
    ) -> bool:
        return await self._repo.delete_value(feature_key, entity_id, entity_type)

    # ── Batch operations ─────────────────────────────────────────

    async def batch_set_features(
        self,
        entity_id: str,
        entity_type: str,
        features: dict[str, Any],
        ttl_seconds: int = 3600,
    ) -> list[FeatureValue]:
        now = datetime.now(timezone.utc)
        values = []
        for key, val in features.items():
            values.append(FeatureValue(
                feature_key=key,
                entity_id=entity_id,
                entity_type=EntityType(entity_type),
                value=val,
                computed_at=now,
                ttl_seconds=ttl_seconds,
            ))
        return await self._repo.batch_save_values(values)

    async def get_features(
        self,
        entity_id: str,
        entity_type: str,
        feature_keys: list[str] | None = None,
    ) -> list[FeatureValue]:
        all_vals = await self._repo.get_values_for_entity(entity_id, entity_type, feature_keys)
        fresh: list[FeatureValue] = []
        for v in all_vals:
            if v.is_expired:
                await self._repo.delete_value(v.feature_key, v.entity_id, v.entity_type.value)
            else:
                fresh.append(v)
        return fresh

    # ── Snapshot ─────────────────────────────────────────────────

    async def get_feature_snapshot(
        self,
        entity_id: str,
        entity_type: str,
    ) -> dict[str, Any]:
        """Return ALL non-expired features for an entity as a dict keyed by feature_key."""
        vals = await self._repo.get_values_for_entity(entity_id, entity_type)
        snapshot: dict[str, Any] = {}
        for v in vals:
            if not v.is_expired:
                snapshot[v.feature_key] = v.value
        return snapshot

    # ── Compute-on-demand ────────────────────────────────────────

    async def compute_and_store(
        self,
        feature_key: str,
        entity_id: str,
        entity_type: str,
        compute_fn: Callable[..., Any],
        ttl_seconds: int = 3600,
        **kwargs: Any,
    ) -> FeatureValue:
        """Run *compute_fn*, store the result, and return the FeatureValue.

        If a fresh (non-expired) value already exists it is returned directly
        without calling *compute_fn*.
        """
        existing = await self.get_feature(feature_key, entity_id, entity_type)
        if existing is not None:
            return existing

        result = await compute_fn(**kwargs) if kwargs else await compute_fn()
        return await self.set_feature(
            feature_key, entity_id, entity_type, result, ttl_seconds
        )
