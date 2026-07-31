"""Regression: GoogleAccountRepository updates must require tenant_id."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.communication_hub.repository import GoogleAccountRepository


@pytest.mark.asyncio
async def test_update_tokens_requires_tenant_id_in_where():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock())
    repo = GoogleAccountRepository(db)
    account_id = uuid4()
    tenant_id = uuid4()

    await repo.update_tokens(
        account_id,
        "enc_access",
        "enc_refresh",
        datetime.now(UTC),
        tenant_id=tenant_id,
    )

    stmt = db.execute.await_args.args[0]
    where_sql = str(stmt.whereclause)
    assert "tenant_id" in where_sql
    assert "id" in where_sql


@pytest.mark.asyncio
async def test_update_methods_signatures_require_tenant():
    sig_tokens = inspect.signature(GoogleAccountRepository.update_tokens)
    assert sig_tokens.parameters["tenant_id"].default is inspect.Parameter.empty

    for name in (
        "update_last_sync",
        "update_history_id",
        "update_calendar_sync_token",
        "deactivate",
    ):
        sig = inspect.signature(getattr(GoogleAccountRepository, name))
        assert sig.parameters["tenant_id"].default is inspect.Parameter.empty, name
