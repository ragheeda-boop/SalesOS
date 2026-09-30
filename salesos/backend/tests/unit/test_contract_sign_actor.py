from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.routers.commercial import ContractSignBody, sign_contract


@pytest.mark.asyncio
async def test_contract_sign_uses_authenticated_user_as_signer() -> None:
    existing = SimpleNamespace(tenant_id="tenant-1")
    service = SimpleNamespace(
        get=AsyncMock(return_value=existing),
        sign=AsyncMock(return_value=existing),
        activate=AsyncMock(return_value=existing),
    )

    with (
        patch("app.routers.commercial._get_contract", return_value=service),
        patch("app.routers.commercial._contract_response", return_value={"status": "active"}),
    ):
        result = await sign_contract(
            contract_id="contract-1",
            body=ContractSignBody(signed_by="spoofed", signed_by_name="Fake User"),
            user_id="user-123",
            tenant_id="tenant-1",
            db=object(),
            _rbac=None,
        )

    assert result == {"status": "active"}
    service.sign.assert_awaited_once_with(
        "contract-1", signed_by_provider="user-123", signed_by_customer="user-123"
    )
    service.activate.assert_awaited_once_with("contract-1")
