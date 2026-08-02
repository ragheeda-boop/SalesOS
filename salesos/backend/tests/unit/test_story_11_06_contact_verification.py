"""STORY-11-06 — Contact Verification (single swappable connector)."""

from __future__ import annotations

import pytest

from app.modules.gtm.verification import VerificationError, normalize_request
from app.modules.gtm.verification_engine import (
    MemVerificationConnector,
    run_verification,
)
from app.modules.gtm.verification_store import MemVerificationStore


@pytest.mark.asyncio
async def test_email_and_phone_verdicts() -> None:
    conn = MemVerificationConnector()
    req = normalize_request(email="ok@acme.sa", phone="+966501234567")
    verdicts = await run_verification(req, conn)
    assert {v.channel for v in verdicts} == {"email", "phone"}
    assert all(v.status == "valid" for v in verdicts)


@pytest.mark.asyncio
async def test_invalid_and_risky_email() -> None:
    conn = MemVerificationConnector()
    bad = await run_verification(normalize_request(email="x@invalid.test"), conn)
    assert bad[0].status == "invalid"
    risky = await run_verification(normalize_request(email="risky.user@acme.sa"), conn)
    assert risky[0].status == "risky"


@pytest.mark.asyncio
async def test_connector_swap_in() -> None:
    """Commodity swap: alternate connector_key replaces default behavior."""
    store = MemVerificationStore()
    alt = MemVerificationConnector(
        key="alt_verify",
        email_overrides={"swap@acme.sa": "invalid"},
    )
    store.bind_connector(alt, default=True)
    assert "alt_verify" in store.connector_keys()
    row = await store.verify(tenant_id="t1", email="swap@acme.sa")
    assert row.provider_key == "alt_verify"
    assert row.verdicts[0].status == "invalid"
    assert row.overall_status == "invalid"


@pytest.mark.asyncio
async def test_store_tenant_isolation() -> None:
    store = MemVerificationStore()
    row = await store.verify(tenant_id="pilot-1", email="a@b.co", phone="+966500000000")
    assert store.get(row.id, tenant_id="pilot-1") is not None
    assert store.get(row.id, tenant_id="other") is None
    assert store.list_for_tenant(tenant_id="other") == []


def test_requires_email_or_phone() -> None:
    with pytest.raises(VerificationError, match="email or phone"):
        normalize_request()


@pytest.mark.asyncio
async def test_unknown_connector_rejected() -> None:
    store = MemVerificationStore()
    with pytest.raises(VerificationError, match="unknown verification connector"):
        await store.verify(
            tenant_id="t1",
            email="a@b.co",
            provider_key="does-not-exist",
        )
