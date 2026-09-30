"""Owner refresh must re-check is_platform_owner before minting a new token."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.modules.identity.router import refresh_token
from app.modules.identity.schemas import RefreshTokenRequest
from app.modules.identity.service import create_owner_refresh_token

USER_ID = "11111111-1111-4111-8111-111111111111"


def _request() -> MagicMock:
    request = MagicMock()
    request.cookies.get.return_value = None
    return request


async def _refresh(monkeypatch, marker):
    async def _probe(_user_id: str):
        return marker

    monkeypatch.setattr("app.database.probe_platform_owner_status", _probe)
    service = MagicMock()
    service.is_token_blacklisted = AsyncMock(return_value=False)
    service.rotate_owner_refresh_token = AsyncMock(return_value=("access", "refresh"))
    service.blacklist_token = AsyncMock()
    body = RefreshTokenRequest(refresh_token=create_owner_refresh_token(USER_ID))
    return await refresh_token(body, _request(), MagicMock(), service), service


@pytest.mark.asyncio
async def test_owner_refresh_rejects_when_marker_cleared(monkeypatch):
    with pytest.raises(HTTPException) as exc:
        await _refresh(monkeypatch, (True, "admin", False))
    assert exc.value.status_code == 403
    assert exc.value.detail == "Owner Platform requires a designated platform owner"


@pytest.mark.asyncio
async def test_owner_refresh_does_not_rotate_when_marker_cleared(monkeypatch):
    service_holder = {}

    async def _probe(_user_id: str):
        return (True, "admin", False)

    monkeypatch.setattr("app.database.probe_platform_owner_status", _probe)
    service = MagicMock()
    service.is_token_blacklisted = AsyncMock(return_value=False)
    service.rotate_owner_refresh_token = AsyncMock(return_value=("access", "refresh"))
    service_holder["service"] = service
    body = RefreshTokenRequest(refresh_token=create_owner_refresh_token(USER_ID))
    with pytest.raises(HTTPException):
        await refresh_token(body, _request(), MagicMock(), service)
    service.rotate_owner_refresh_token.assert_not_called()


@pytest.mark.asyncio
async def test_owner_refresh_rotates_while_marker_holds(monkeypatch):
    result, service = await _refresh(monkeypatch, (True, "admin", True))
    assert result.access_token == "access"
    service.rotate_owner_refresh_token.assert_awaited_once()
