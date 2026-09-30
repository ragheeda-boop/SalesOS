"""Self-service register must never join an existing tenant by UUID.

An unauthenticated caller who knows another tenant's id could previously
register into it and read that tenant's data. Joining an existing tenant is
only possible through the admin-gated /invite endpoint.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.modules.identity.router import register
from app.modules.identity.schemas import UserCreate


def _body(tenant_id: uuid.UUID | None) -> UserCreate:
    return UserCreate(
        email="pilot.seller@example.com",
        password="Str0ng!Passw0rd#2026",
        full_name="Pilot Seller",
        tenant_id=tenant_id,
    )


async def test_register_with_existing_tenant_id_is_rejected_before_any_db_write() -> None:
    db = MagicMock()
    db.execute = AsyncMock()
    service = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await register(
            _body(uuid.uuid4()),
            request=MagicMock(),
            response=MagicMock(),
            service=service,
            db=db,
        )

    assert exc.value.status_code == 400
    assert "tenant_id_not_allowed" in exc.value.detail
    db.execute.assert_not_awaited()
    service.assert_not_called()
