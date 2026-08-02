"""STORY-08-03 — FieldMappingConfig persistence (tenant-scoped).

Always filters by tenant_id. Does not touch DEC-085. Not Production GO.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integration_hub.field_mapping import (
    mappings_to_json,
    parse_field_mappings,
)
from app.modules.integration_hub.models import FieldMappingConfigModel


class FieldMappingConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID | str,
        connection_id: uuid.UUID | str,
        model: str,
        mappings: list[Mapping[str, Any]] | list[dict[str, Any]],
        baseline_fields: list[str] | None = None,
        version: int = 1,
    ) -> FieldMappingConfigModel:
        tid = uuid.UUID(str(tenant_id))
        cid = uuid.UUID(str(connection_id))
        model_key = (model or "").strip()
        if not model_key or len(model_key) > 128:
            raise ValueError("model required (max 128)")
        entries = parse_field_mappings(list(mappings))
        if not entries:
            raise ValueError("mappings must not be empty")
        ver = int(version)
        if ver < 1:
            raise ValueError("version must be >= 1")
        if baseline_fields is None:
            baseline = sorted({e.external for e in entries})
        else:
            baseline = sorted({str(x).strip() for x in baseline_fields if str(x).strip()})
        row = FieldMappingConfigModel(
            id=uuid.uuid4(),
            tenant_id=tid,
            connection_id=cid,
            model=model_key,
            version=ver,
            mappings=mappings_to_json(entries),
            baseline_fields=baseline,
            is_active=True,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_for_tenant(
        self,
        mapping_id: uuid.UUID | str,
        *,
        tenant_id: uuid.UUID | str,
    ) -> FieldMappingConfigModel | None:
        mid = uuid.UUID(str(mapping_id))
        tid = uuid.UUID(str(tenant_id))
        return (
            await self.session.execute(
                select(FieldMappingConfigModel).where(
                    FieldMappingConfigModel.id == mid,
                    FieldMappingConfigModel.tenant_id == tid,
                )
            )
        ).scalar_one_or_none()

    async def get_active_for_connection_model(
        self,
        *,
        tenant_id: uuid.UUID | str,
        connection_id: uuid.UUID | str,
        model: str,
    ) -> FieldMappingConfigModel | None:
        tid = uuid.UUID(str(tenant_id))
        cid = uuid.UUID(str(connection_id))
        model_key = (model or "").strip()
        return (
            await self.session.execute(
                select(FieldMappingConfigModel)
                .where(
                    FieldMappingConfigModel.tenant_id == tid,
                    FieldMappingConfigModel.connection_id == cid,
                    FieldMappingConfigModel.model == model_key,
                    FieldMappingConfigModel.is_active.is_(True),
                )
                .order_by(FieldMappingConfigModel.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
