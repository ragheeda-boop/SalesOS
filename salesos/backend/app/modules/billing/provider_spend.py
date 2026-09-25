"""Durable, fail-closed spend reservations for external data providers.

This module deliberately does not call providers. A provider adapter must reserve
and commit before dispatch, transition to IN_FLIGHT, then settle, mark UNKNOWN,
or release only when the provider confirms that no billable request occurred.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_CONTROL_CHARACTER_LIMIT = 32


_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_SCOPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class ProviderSpendError(ValueError):
    """A provider spend request violates its configured budget boundary."""


class ProviderReservationNotDispatchableError(ProviderSpendError):
    """An idempotent reservation was already dispatched or resolved."""


@dataclass(frozen=True)
class ProviderSpendRequest:
    tenant_id: str | uuid.UUID
    provider_key: str
    operation_key: str
    billing_scope_key: str
    price_card_version: str
    billable_units: int
    idempotency_key: str
    request_fingerprint: str


@dataclass(frozen=True)
class ProviderSpendReservation:
    reservation_id: uuid.UUID
    status: str
    reused: bool
    estimated_micros: int
    currency: str


class ProviderSpendCoordinator:
    """Commit reservations in a dedicated transaction before provider I/O."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def reserve(
        self,
        request: ProviderSpendRequest,
    ) -> ProviderSpendReservation:
        tenant = _tenant_uuid(request.tenant_id)
        _match(_KEY_RE, request.provider_key, "provider_key")
        _match(_KEY_RE, request.operation_key, "operation_key")
        _match(_SCOPE_RE, request.billing_scope_key, "billing_scope_key")
        _match(_VERSION_RE, request.price_card_version, "price_card_version")
        _bounded_text(request.idempotency_key, "idempotency_key", 128)
        if not isinstance(request.billable_units, int) or isinstance(request.billable_units, bool):
            raise ProviderSpendError("billable_units must be a positive integer")
        if request.billable_units <= 0:
            raise ProviderSpendError("billable_units must be a positive integer")
        if not isinstance(request.request_fingerprint, str) or not _HASH_RE.fullmatch(
            request.request_fingerprint
        ):
            raise ProviderSpendError("request_fingerprint must be a lowercase SHA-256 hex digest")

        row = await self._call(
            tenant,
            """
            SELECT reservation_id, reservation_status, reused, estimated_micros, currency
            FROM reserve_provider_spend(
                :tenant_id, :provider_key, :operation_key, :billing_scope_key,
                :price_card_version, :billable_units, :idempotency_key,
                :request_fingerprint
            )
            """,
            {
                "tenant_id": tenant,
                "provider_key": request.provider_key,
                "operation_key": request.operation_key,
                "billing_scope_key": request.billing_scope_key,
                "price_card_version": request.price_card_version,
                "billable_units": request.billable_units,
                "idempotency_key": request.idempotency_key,
                "request_fingerprint": request.request_fingerprint,
            },
        )
        result = ProviderSpendReservation(
            reservation_id=uuid.UUID(str(row["reservation_id"])),
            status=str(row["reservation_status"]),
            reused=bool(row["reused"]),
            estimated_micros=int(row["estimated_micros"]),
            currency=str(row["currency"]).strip(),
        )
        if result.reused:
            raise ProviderReservationNotDispatchableError(
                f"idempotent reservation already exists as {result.status.lower()}"
            )
        return result

    async def mark_in_flight(
        self, *, tenant_id: str | uuid.UUID, reservation_id: str | uuid.UUID
    ) -> None:
        tenant = _tenant_uuid(tenant_id)
        reservation = _tenant_uuid(reservation_id)
        await self._call(
            tenant,
            "SELECT mark_provider_spend_in_flight(:tenant_id, :reservation_id)",
            {"tenant_id": tenant, "reservation_id": reservation},
        )

    async def mark_unknown(
        self, *, tenant_id: str | uuid.UUID, reservation_id: str | uuid.UUID
    ) -> None:
        tenant = _tenant_uuid(tenant_id)
        reservation = _tenant_uuid(reservation_id)
        await self._call(
            tenant,
            "SELECT mark_provider_spend_unknown(:tenant_id, :reservation_id)",
            {"tenant_id": tenant, "reservation_id": reservation},
        )

    async def settle(
        self,
        *,
        tenant_id: str | uuid.UUID,
        reservation_id: str | uuid.UUID,
        actual_micros: int,
    ) -> bool:
        tenant = _tenant_uuid(tenant_id)
        reservation = _tenant_uuid(reservation_id)
        if not isinstance(actual_micros, int) or isinstance(actual_micros, bool):
            raise ProviderSpendError("actual_micros must be a non-negative integer")
        if actual_micros < 0:
            raise ProviderSpendError("actual_micros must be a non-negative integer")
        row = await self._call(
            tenant,
            """
            SELECT over_budget FROM settle_provider_spend(
                :tenant_id, :reservation_id, :actual_micros
            )
            """,
            {
                "tenant_id": tenant,
                "reservation_id": reservation,
                "actual_micros": actual_micros,
            },
        )
        return bool(row["over_budget"])

    async def release_confirmed_no_charge(
        self,
        *,
        tenant_id: str | uuid.UUID,
        reservation_id: str | uuid.UUID,
        reason: str,
        provider_confirmed_no_charge: bool,
    ) -> None:
        tenant = _tenant_uuid(tenant_id)
        reservation = _tenant_uuid(reservation_id)
        if provider_confirmed_no_charge is not True:
            raise ProviderSpendError(
                "reservation release requires explicit confirmation that no charge occurred"
            )
        _bounded_text(reason, "reason", 240, minimum=8)
        await self._call(
            tenant,
            """
            SELECT release_provider_spend(
                :tenant_id, :reservation_id, :reason
            )
            """,
            {"tenant_id": tenant, "reservation_id": reservation, "reason": reason.strip()},
        )

    async def _call(
        self,
        tenant_id: uuid.UUID,
        statement: str,
        parameters: dict[str, Any],
    ) -> Any:
        async with self._session_factory() as session, session.begin():
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            result = await session.execute(text(statement), parameters)
            return result.mappings().one()


def _tenant_uuid(value: str | uuid.UUID) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ProviderSpendError("tenant_id and reservation_id must be UUIDs") from exc


def _match(pattern: re.Pattern[str], value: str, label: str) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ProviderSpendError(f"{label} has an invalid format")


def _bounded_text(value: str, label: str, maximum: int, *, minimum: int = 1) -> None:
    if (
        not isinstance(value, str)
        or not minimum <= len(value.strip()) <= maximum
        or any(ord(character) < _CONTROL_CHARACTER_LIMIT for character in value)
    ):
        raise ProviderSpendError(f"{label} must be bounded non-empty text")
