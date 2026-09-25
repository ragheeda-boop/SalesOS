"""Validation tests for the durable provider spend coordinator."""

from __future__ import annotations

import uuid
from dataclasses import replace
from unittest.mock import AsyncMock

import pytest

from app.modules.billing.provider_spend import (
    ProviderReservationNotDispatchableError,
    ProviderSpendCoordinator,
    ProviderSpendError,
    ProviderSpendRequest,
)

TENANT_ID = uuid.UUID("8ba41a63-2164-4402-a7fc-95dc30b17479")
VALID_RESERVATION = ProviderSpendRequest(
    tenant_id=TENANT_ID,
    provider_key="scout",
    operation_key="domain_lookup",
    billing_scope_key="scout-prod",
    price_card_version="quote-2026-09-1",
    billable_units=1,
    idempotency_key="request-1",
    request_fingerprint="a" * 64,
)


def coordinator() -> ProviderSpendCoordinator:
    # Every validation case must fail before any database session is opened.
    return ProviderSpendCoordinator(None)  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("units", [0, -1, True, 1.5, "2"])
async def test_reservation_requires_positive_integer_units(units):
    with pytest.raises(ProviderSpendError, match="billable_units"):
        await coordinator().reserve(replace(VALID_RESERVATION, billable_units=units))


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["", "GoogleMaps", "a", "bad-provider", "x" * 65])
async def test_reservation_rejects_unknown_or_malformed_provider_keys(provider):
    with pytest.raises(ProviderSpendError, match="provider_key"):
        await coordinator().reserve(replace(VALID_RESERVATION, provider_key=provider))


@pytest.mark.asyncio
@pytest.mark.parametrize("fingerprint", ["", "A" * 64, "a" * 63, "a" * 65])
async def test_reservation_requires_lowercase_sha256_fingerprint(fingerprint):
    with pytest.raises(ProviderSpendError, match="request_fingerprint"):
        await coordinator().reserve(replace(VALID_RESERVATION, request_fingerprint=fingerprint))


@pytest.mark.asyncio
async def test_reservation_rejects_non_uuid_tenant_before_database_access():
    with pytest.raises(ProviderSpendError, match="UUIDs"):
        await coordinator().reserve(replace(VALID_RESERVATION, tenant_id="not-a-uuid"))


@pytest.mark.asyncio
async def test_reused_reserved_idempotency_key_cannot_dispatch_twice():
    instance = coordinator()
    instance._call = AsyncMock(
        return_value={
            "reservation_id": uuid.uuid4(),
            "reservation_status": "RESERVED",
            "reused": True,
            "estimated_micros": 2000,
            "currency": "USD",
        }
    )

    with pytest.raises(ProviderReservationNotDispatchableError, match="already exists"):
        await instance.reserve(VALID_RESERVATION)


@pytest.mark.asyncio
async def test_release_requires_explicit_provider_confirmation_of_no_charge():
    with pytest.raises(ProviderSpendError, match="explicit confirmation"):
        await coordinator().release_confirmed_no_charge(
            tenant_id=TENANT_ID,
            reservation_id=uuid.uuid4(),
            reason="Provider timed out.",
            provider_confirmed_no_charge=False,
        )


@pytest.mark.asyncio
async def test_release_requires_a_bounded_audit_reason():
    with pytest.raises(ProviderSpendError, match="reason"):
        await coordinator().release_confirmed_no_charge(
            tenant_id=TENANT_ID,
            reservation_id=uuid.uuid4(),
            reason="no",
            provider_confirmed_no_charge=True,
        )


@pytest.mark.asyncio
async def test_settlement_cost_must_be_nonnegative_integer():
    with pytest.raises(ProviderSpendError, match="actual_micros"):
        await coordinator().settle(
            tenant_id=TENANT_ID,
            reservation_id=uuid.uuid4(),
            actual_micros=-1,
        )
