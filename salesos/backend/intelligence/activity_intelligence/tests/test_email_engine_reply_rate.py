"""EmailEngine reply-rate must be thread-based when DB is available."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from intelligence.activity_intelligence.engine.email_engine import EmailEngine


@pytest.mark.asyncio
async def test_reply_rate_uses_thread_counts_not_inbound_total_ratio():
    tenant_id = str(uuid4())
    company_id = str(uuid4())

    mock_db = AsyncMock()
    result = MagicMock()
    result.mappings.return_value.one.return_value = {
        "inbound_threads": 4,
        "replied_threads": 1,
    }
    captured = []

    async def execute(sql, params=None):
        captured.append({"sql": str(getattr(sql, "text", sql)), "params": dict(params or {})})
        return result

    mock_db.execute = execute

    reader = MagicMock()
    reader.db = mock_db
    # If engine fell back to volume ratio, these would be used incorrectly.
    reader.count_by_company = AsyncMock(side_effect=[10, 9])  # total=10, inbound=9

    engine = EmailEngine(email_reader=reader)
    rate = await engine.get_reply_rate(company_id, tenant_id)

    assert rate == 0.25  # 1/4 threads, NOT 9/10
    assert captured
    assert captured[0]["params"]["tid"] == tenant_id
    assert "thread_id" in captured[0]["sql"]
    assert "tenant_id" in captured[0]["sql"]
