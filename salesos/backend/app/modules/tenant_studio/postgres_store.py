"""Tenant-scoped PostgreSQL persistence for AI Studio configuration documents."""

from __future__ import annotations

import json
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DocumentType = Literal["prompt_library", "ai_policies"]


class PostgresTenantStudioStore:
    """Persist small, versioned AI Studio documents under tenant RLS."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _tenant_uuid(tenant_id: str) -> UUID:
        try:
            return UUID(str(tenant_id))
        except (TypeError, ValueError) as exc:
            raise ValueError("tenant_id must be a UUID") from exc

    async def get(
        self, *, tenant_id: str, document_type: DocumentType, document_key: str
    ) -> dict[str, Any] | None:
        result = await self.db.execute(
            text(
                "SELECT payload FROM tenant_studio_documents "
                "WHERE tenant_id = :tenant_id AND document_type = :document_type "
                "AND document_key = :document_key"
            ),
            {
                "tenant_id": self._tenant_uuid(tenant_id),
                "document_type": document_type,
                "document_key": document_key,
            },
        )
        row = result.mappings().one_or_none()
        return dict(row["payload"]) if row is not None else None

    async def list_for_tenant(
        self, *, tenant_id: str, document_type: DocumentType
    ) -> list[dict[str, Any]]:
        result = await self.db.execute(
            text(
                "SELECT payload FROM tenant_studio_documents "
                "WHERE tenant_id = :tenant_id AND document_type = :document_type "
                "ORDER BY updated_at DESC, document_key"
            ),
            {"tenant_id": self._tenant_uuid(tenant_id), "document_type": document_type},
        )
        return [dict(row["payload"]) for row in result.mappings().all()]

    async def create(
        self,
        *,
        tenant_id: str,
        document_type: DocumentType,
        document_key: str,
        payload: dict[str, Any],
        logical_key: str | None = None,
    ) -> dict[str, Any] | None:
        """Insert only; return None when the tenant-scoped key already exists."""
        result = await self.db.execute(
            text(
                "INSERT INTO tenant_studio_documents "
                "(id, tenant_id, document_type, document_key, logical_key, payload, schema_version) "
                "VALUES (:id, :tenant_id, :document_type, :document_key, :logical_key, "
                "CAST(:payload AS jsonb), 1) "
                "ON CONFLICT DO NOTHING "
                "RETURNING payload"
            ),
            {
                "id": uuid4(),
                "tenant_id": self._tenant_uuid(tenant_id),
                "document_type": document_type,
                "document_key": document_key,
                "logical_key": logical_key,
                "payload": json.dumps(payload, ensure_ascii=False),
            },
        )
        row = result.mappings().one_or_none()
        return dict(row["payload"]) if row is not None else None

    async def replace_if_version(
        self,
        *,
        tenant_id: str,
        document_type: DocumentType,
        document_key: str,
        payload: dict[str, Any],
        expected_schema_version: int,
        logical_key: str | None = None,
    ) -> dict[str, Any] | None:
        result = await self.db.execute(
            text(
                "UPDATE tenant_studio_documents "
                "SET logical_key = :logical_key, payload = CAST(:payload AS jsonb), "
                "schema_version = schema_version + 1, updated_at = now() "
                "WHERE tenant_id = :tenant_id AND document_type = :document_type "
                "AND document_key = :document_key AND schema_version = :expected_schema_version "
                "RETURNING payload"
            ),
            {
                "tenant_id": self._tenant_uuid(tenant_id),
                "document_type": document_type,
                "document_key": document_key,
                "logical_key": logical_key,
                "expected_schema_version": expected_schema_version,
                "payload": json.dumps(payload, ensure_ascii=False),
            },
        )
        row = result.mappings().one_or_none()
        return dict(row["payload"]) if row is not None else None

    async def delete(
        self, *, tenant_id: str, document_type: DocumentType, document_key: str
    ) -> bool:
        result = await self.db.execute(
            text(
                "DELETE FROM tenant_studio_documents "
                "WHERE tenant_id = :tenant_id AND document_type = :document_type "
                "AND document_key = :document_key RETURNING document_key"
            ),
            {
                "tenant_id": self._tenant_uuid(tenant_id),
                "document_type": document_type,
                "document_key": document_key,
            },
        )
        return result.scalar_one_or_none() is not None
