from __future__ import annotations

import inspect
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.dependencies import get_current_user_id
from app.modules.company import router as company_router
from app.modules.company.service import CompanyService


def test_company_create_and_update_routes_require_verified_actor():
    for route in (company_router.create_company, company_router.update_company):
        assert inspect.signature(route).parameters["user_id"].default.dependency is (
            get_current_user_id
        )


@pytest.mark.asyncio
async def test_company_update_audit_records_human_actor(monkeypatch):
    db = SimpleNamespace(flush=AsyncMock(), refresh=AsyncMock())
    audit = SimpleNamespace(record=AsyncMock())
    monkeypatch.setattr(
        "app.modules.company.service.AuditTrail", lambda _db: audit
    )
    company = SimpleNamespace(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), city="Old City"
    )
    service = CompanyService(db)
    service.get_company = AsyncMock(return_value=company)

    await service.update_company(
        str(company.id),
        {"city": "Riyadh"},
        tenant_id=str(company.tenant_id),
        performed_by="verified-user-1",
    )

    audit.record.assert_awaited_once()
    assert audit.record.await_args.kwargs["performed_by"] == "verified-user-1"
    assert audit.record.await_args.kwargs["changes"] == {"city": "Riyadh"}
