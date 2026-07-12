"""PostgreSQL Feature Store repository implementation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.database import Base

from .models import EntityType, FeatureDefinition, FeatureType, FeatureValue
from .repository import FeatureStoreRepository


class FeatureDefinitionModel(Base):
    __tablename__ = "feature_definitions"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feature_type: Mapped[str] = mapped_column(String(50), default="numeric")
    domain: Mapped[str] = mapped_column(String(100), default="general")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FeatureValueModel(Base):
    __tablename__ = "feature_values"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    feature_key: Mapped[str] = mapped_column(
        String(255), ForeignKey("feature_definitions.key"), nullable=False
    )
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ttl_seconds: Mapped[int] = mapped_column(Integer, default=3600)

    __table_args__ = (
        Index(
            "idx_feature_values_lookup",
            "entity_type",
            "entity_id",
            "feature_key",
        ),
    )


from sqlalchemy.orm import Mapped, mapped_column  # noqa: E402


class PostgresFeatureStoreRepository(FeatureStoreRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_definition(self, definition: FeatureDefinition) -> FeatureDefinition:
        stmt = select(FeatureDefinitionModel).where(FeatureDefinitionModel.key == definition.key)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = definition.name
            model.description = definition.description
            model.feature_type = definition.feature_type.value
            model.domain = definition.domain
        else:
            model = FeatureDefinitionModel(
                key=definition.key,
                name=definition.name,
                description=definition.description,
                feature_type=definition.feature_type.value,
                domain=definition.domain,
                created_at=definition.created_at,
            )
            self.session.add(model)
        await self.session.flush()
        return definition

    async def get_definition(self, key: str) -> Optional[FeatureDefinition]:
        stmt = select(FeatureDefinitionModel).where(FeatureDefinitionModel.key == key)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return FeatureDefinition(
            key=model.key,
            name=model.name,
            description=model.description or "",
            feature_type=FeatureType(model.feature_type),
            domain=model.domain,
            created_at=model.created_at,
        )

    async def delete_definition(self, key: str) -> bool:
        stmt = select(FeatureDefinitionModel).where(FeatureDefinitionModel.key == key)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def list_definitions(self, domain: str | None = None) -> list[FeatureDefinition]:
        stmt = select(FeatureDefinitionModel)
        if domain:
            stmt = stmt.where(FeatureDefinitionModel.domain == domain)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [
            FeatureDefinition(
                key=m.key,
                name=m.name,
                description=m.description or "",
                feature_type=FeatureType(m.feature_type),
                domain=m.domain,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def save_value(self, value: FeatureValue) -> FeatureValue:
        lookup_id = f"{value.entity_type.value}:{value.entity_id}:{value.feature_key}"
        stmt = select(FeatureValueModel).where(FeatureValueModel.id == lookup_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.value = value.value
            model.computed_at = value.computed_at
            model.ttl_seconds = value.ttl_seconds
        else:
            model = FeatureValueModel(
                id=lookup_id,
                feature_key=value.feature_key,
                entity_id=value.entity_id,
                entity_type=value.entity_type.value,
                value=value.value,
                computed_at=value.computed_at,
                ttl_seconds=value.ttl_seconds,
            )
            self.session.add(model)
        await self.session.flush()
        return value

    async def get_value(
        self, feature_key: str, entity_id: str, entity_type: str
    ) -> Optional[FeatureValue]:
        stmt = select(FeatureValueModel).where(
            FeatureValueModel.feature_key == feature_key,
            FeatureValueModel.entity_id == entity_id,
            FeatureValueModel.entity_type == entity_type,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return FeatureValue(
            feature_key=model.feature_key,
            entity_id=model.entity_id,
            entity_type=EntityType(model.entity_type),
            value=model.value,
            computed_at=model.computed_at,
            ttl_seconds=model.ttl_seconds,
        )

    async def get_values_for_entity(
        self, entity_id: str, entity_type: str, feature_keys: list[str] | None = None
    ) -> list[FeatureValue]:
        stmt = select(FeatureValueModel).where(
            FeatureValueModel.entity_id == entity_id,
            FeatureValueModel.entity_type == entity_type,
        )
        if feature_keys:
            stmt = stmt.where(FeatureValueModel.feature_key.in_(feature_keys))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [
            FeatureValue(
                feature_key=m.feature_key,
                entity_id=m.entity_id,
                entity_type=EntityType(m.entity_type),
                value=m.value,
                computed_at=m.computed_at,
                ttl_seconds=m.ttl_seconds,
            )
            for m in models
        ]

    async def batch_save_values(self, values: list[FeatureValue]) -> list[FeatureValue]:
        saved: list[FeatureValue] = []
        for v in values:
            saved.append(await self.save_value(v))
        return saved

    async def delete_value(
        self, feature_key: str, entity_id: str, entity_type: str
    ) -> bool:
        lookup_id = f"{entity_type}:{entity_id}:{feature_key}"
        stmt = select(FeatureValueModel).where(FeatureValueModel.id == lookup_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False
