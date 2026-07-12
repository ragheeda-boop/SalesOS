from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional

from .models import FeatureDefinition, FeatureValue


class FeatureStoreRepository(ABC):
    @abstractmethod
    async def save_definition(self, definition: FeatureDefinition) -> FeatureDefinition: ...

    @abstractmethod
    async def get_definition(self, key: str) -> Optional[FeatureDefinition]: ...

    @abstractmethod
    async def delete_definition(self, key: str) -> bool: ...

    @abstractmethod
    async def list_definitions(self, domain: str | None = None) -> list[FeatureDefinition]: ...

    @abstractmethod
    async def save_value(self, value: FeatureValue) -> FeatureValue: ...

    @abstractmethod
    async def get_value(
        self, feature_key: str, entity_id: str, entity_type: str
    ) -> Optional[FeatureValue]: ...

    @abstractmethod
    async def get_values_for_entity(
        self, entity_id: str, entity_type: str, feature_keys: list[str] | None = None
    ) -> list[FeatureValue]: ...

    @abstractmethod
    async def batch_save_values(self, values: list[FeatureValue]) -> list[FeatureValue]: ...

    @abstractmethod
    async def delete_value(
        self, feature_key: str, entity_id: str, entity_type: str
    ) -> bool: ...


class InMemoryFeatureStoreRepository(FeatureStoreRepository):
    def __init__(self):
        self._definitions: dict[str, FeatureDefinition] = {}
        self._values: dict[tuple[str, str, str], FeatureValue] = {}

    async def save_definition(self, definition: FeatureDefinition) -> FeatureDefinition:
        self._definitions[definition.key] = definition
        return definition

    async def get_definition(self, key: str) -> Optional[FeatureDefinition]:
        return self._definitions.get(key)

    async def delete_definition(self, key: str) -> bool:
        return self._definitions.pop(key, None) is not None

    async def list_definitions(self, domain: str | None = None) -> list[FeatureDefinition]:
        defs = list(self._definitions.values())
        if domain:
            defs = [d for d in defs if d.domain == domain]
        return defs

    async def save_value(self, value: FeatureValue) -> FeatureValue:
        key = (value.feature_key, value.entity_id, value.entity_type.value)
        self._values[key] = value
        return value

    async def get_value(
        self, feature_key: str, entity_id: str, entity_type: str
    ) -> Optional[FeatureValue]:
        return self._values.get((feature_key, entity_id, entity_type))

    async def get_values_for_entity(
        self, entity_id: str, entity_type: str, feature_keys: list[str] | None = None
    ) -> list[FeatureValue]:
        results = []
        for (fk, eid, et), val in self._values.items():
            if eid == entity_id and et == entity_type:
                if feature_keys is None or fk in feature_keys:
                    results.append(val)
        return results

    async def batch_save_values(self, values: list[FeatureValue]) -> list[FeatureValue]:
        saved = []
        for v in values:
            saved.append(await self.save_value(v))
        return saved

    async def delete_value(
        self, feature_key: str, entity_id: str, entity_type: str
    ) -> bool:
        return self._values.pop((feature_key, entity_id, entity_type), None) is not None
