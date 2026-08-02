"""STORY-08-02 — ExternalSystemConnection service (tenant-scoped).

Always filters by tenant_id (app-layer isolation). Fernet via sdk.security.
Does not invent secrets. Does not touch DEC-085. Not Production GO.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.integration_hub.connection_secrets import (
    assert_safe_connection_config,
    decrypt_credentials_blob,
    encrypt_credentials_blob,
    normalize_credential_ref,
)
from app.modules.integration_hub.models import ExternalSystemConnectionModel


def _encryption_secret() -> str:
    # Prefer dedicated override when ops set it; else existing app secret_key.
    dedicated = (getattr(settings, "integration_hub_encryption_key", "") or "").strip()
    if dedicated:
        return dedicated
    return (settings.secret_key or "").strip()


class ExternalSystemConnectionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID | str,
        connector_key: str,
        name: str,
        credential_ref: str,
        connection_config: Mapping[str, Any] | None = None,
        credentials: Mapping[str, Any] | None = None,
    ) -> ExternalSystemConnectionModel:
        tid = uuid.UUID(str(tenant_id))
        key = (connector_key or "").strip().lower()
        if not key or len(key) > 64:
            raise ValueError("connector_key required (max 64)")
        label = (name or "").strip()
        if not label or len(label) > 128:
            raise ValueError("name required (max 128)")
        ref = normalize_credential_ref(credential_ref)
        cfg = assert_safe_connection_config(connection_config)
        enc = encrypt_credentials_blob(credentials, secret=_encryption_secret())
        row = ExternalSystemConnectionModel(
            id=uuid.uuid4(),
            tenant_id=tid,
            connector_key=key,
            name=label,
            credential_ref=ref,
            credentials_encrypted=enc,
            connection_config=cfg,
            cursor_state={},
            is_active=True,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_for_tenant(
        self,
        connection_id: uuid.UUID | str,
        *,
        tenant_id: uuid.UUID | str,
    ) -> ExternalSystemConnectionModel | None:
        """Return connection only when it belongs to tenant_id."""
        cid = uuid.UUID(str(connection_id))
        tid = uuid.UUID(str(tenant_id))
        row = (
            await self.session.execute(
                select(ExternalSystemConnectionModel).where(
                    ExternalSystemConnectionModel.id == cid,
                    ExternalSystemConnectionModel.tenant_id == tid,
                )
            )
        ).scalar_one_or_none()
        return row

    async def list_for_tenant(
        self,
        *,
        tenant_id: uuid.UUID | str,
        connector_key: str | None = None,
        limit: int = 100,
    ) -> list[ExternalSystemConnectionModel]:
        tid = uuid.UUID(str(tenant_id))
        q = select(ExternalSystemConnectionModel).where(
            ExternalSystemConnectionModel.tenant_id == tid
        )
        if connector_key:
            q = q.where(
                ExternalSystemConnectionModel.connector_key == connector_key.strip().lower()
            )
        q = q.order_by(ExternalSystemConnectionModel.created_at.desc()).limit(
            max(1, min(int(limit), 500))
        )
        return list((await self.session.execute(q)).scalars().all())

    def reveal_credentials(self, row: ExternalSystemConnectionModel) -> dict[str, Any]:
        """Decrypt credentials envelope (caller must already be tenant-authorized)."""
        return decrypt_credentials_blob(row.credentials_encrypted, secret=_encryption_secret())

    async def set_cursor(
        self,
        connection_id: uuid.UUID | str,
        *,
        tenant_id: uuid.UUID | str,
        model: str,
        watermark: str,
    ) -> ExternalSystemConnectionModel | None:
        row = await self.get_for_tenant(connection_id, tenant_id=tenant_id)
        if row is None:
            return None
        model_key = (model or "").strip()
        if not model_key:
            raise ValueError("model required")
        state = dict(row.cursor_state or {})
        state[model_key] = str(watermark)
        row.cursor_state = state
        await self.session.flush()
        return row
