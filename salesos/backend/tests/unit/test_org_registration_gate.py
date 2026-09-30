"""Organization registration waits for the platform owner."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.modules.identity.org_registration import (
    consume_approved_organization,
    decide_org_registration,
    lock_approved_organization,
)
from app.modules.identity.router import register
from app.modules.identity.schemas import UserCreate


def _body() -> UserCreate:
    return UserCreate(
        email="sultan@muhide.example",
        password="Str0ng!Passw0rd#2026",
        full_name="Sultan",
        organization_name="Muhide",
    )


def _db_with_row(row: dict | None) -> MagicMock:
    db = MagicMock()
    result = MagicMock()
    result.mappings.return_value.first.return_value = row
    result.first.return_value = (row["id"],) if row else None
    db.execute = AsyncMock(return_value=result)
    return db


async def test_lock_without_approval_is_forbidden() -> None:
    db = _db_with_row(None)
    with pytest.raises(HTTPException) as exc:
        await lock_approved_organization(db, email="sultan@muhide.example", organization_name="Muhide")
    assert exc.value.status_code == 403
    assert "owner_approval_required" in exc.value.detail


async def test_lock_rejects_a_different_organization_name() -> None:
    db = _db_with_row({"id": uuid.uuid4(), "organization_name": "Muhide"})
    with pytest.raises(HTTPException) as exc:
        await lock_approved_organization(
            db, email="sultan@muhide.example", organization_name="Other Co"
        )
    assert exc.value.status_code == 403
    assert "organization_name_mismatch" in exc.value.detail


async def test_register_does_not_create_a_user_without_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _deny(*_args, **_kwargs):
        raise HTTPException(status_code=403, detail="register.owner_approval_required")

    monkeypatch.setattr(
        "app.modules.identity.router.lock_approved_organization",
        _deny,
    )
    db = MagicMock()
    db.execute = AsyncMock()
    service = MagicMock()
    service.create_user = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await register(
            _body(),
            request=MagicMock(),
            response=MagicMock(),
            service=service,
            db=db,
        )

    assert exc.value.status_code == 403
    service.create_user.assert_not_awaited()


async def test_register_names_the_tenant_from_the_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    async def _lock(*_args, **_kwargs):
        return ("approval-1", "Muhide")

    async def _consume(*_args, **kwargs):
        seen["consumed"] = kwargs["tenant_id"]

    monkeypatch.setattr("app.modules.identity.router.lock_approved_organization", _lock)
    monkeypatch.setattr("app.modules.identity.router.consume_approved_organization", _consume)

    db = MagicMock()

    async def _execute(statement, params=None, *_a, **_k):
        sql = str(statement)
        if "INSERT INTO tenants" in sql:
            seen["tenant_name"] = params["name"]
        return MagicMock()

    db.execute = AsyncMock(side_effect=_execute)
    service = MagicMock()
    service.create_user = AsyncMock(side_effect=HTTPException(status_code=500, detail="stop"))

    with pytest.raises(HTTPException) as exc:
        await register(
            _body(),
            request=MagicMock(),
            response=MagicMock(),
            service=service,
            db=db,
        )

    assert exc.value.status_code == 500
    assert seen["tenant_name"] == "Muhide"
    assert seen["consumed"]


async def test_reject_requires_a_reason() -> None:
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await decide_org_registration(
            db,
            request_id=uuid.uuid4(),
            decision="reject",
            reason="  ",
            decided_by=str(uuid.uuid4()),
        )
    assert exc.value.status_code == 422
    db.execute.assert_not_called()


async def test_consume_conflict_when_the_row_is_no_longer_approved() -> None:
    db = MagicMock()
    result = MagicMock()
    result.first.return_value = None
    db.execute = AsyncMock(return_value=result)
    with pytest.raises(HTTPException) as exc:
        await consume_approved_organization(
            db, approval_id=str(uuid.uuid4()), tenant_id=str(uuid.uuid4())
        )
    assert exc.value.status_code == 409
