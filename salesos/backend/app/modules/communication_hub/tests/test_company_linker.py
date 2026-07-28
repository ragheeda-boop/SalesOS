"""company_linker: tenant scoping + parameterized domain matching."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.communication_hub.company_linker import (
    extract_domains,
    resolve_company_ids_for_addresses,
)


def test_extract_domains_skips_free_and_invalid():
    domains = extract_domains(
        [
            "a@acme.com",
            "b@gmail.com",
            "bad",
            "c@evil.com'; DROP TABLE companies;--",
            "d@ok.io",
        ]
    )
    assert "acme.com" in domains
    assert "ok.io" in domains
    assert "gmail.com" not in domains
    assert all(all(c.isalnum() or c in ".-" for c in d) for d in domains)


@pytest.mark.asyncio
async def test_resolve_binds_tenant_and_domain_params():
    captured: list[dict] = []
    db = AsyncMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = [{"id": str(uuid4())}]

    async def execute(sql, params=None):
        captured.append({"sql": str(getattr(sql, "text", sql)), "params": dict(params or {})})
        return result

    db.execute = execute
    tenant_id = uuid4()
    ids = await resolve_company_ids_for_addresses(
        db, tenant_id, ["alice@partner.example", "bob@other.co"]
    )
    assert ids
    cap = captured[-1]
    assert cap["params"]["tid"] == str(tenant_id)
    assert "tenant_id = :tid" in cap["sql"]
    # Domain values must be params, not raw SQL fragments.
    assert "partner.example" not in cap["sql"]
    assert any(v.endswith("partner.example%") for v in cap["params"].values())
