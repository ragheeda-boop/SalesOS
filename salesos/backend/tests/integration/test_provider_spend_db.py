"""PostgreSQL proof for atomic, tenant-scoped provider spend reservations."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.modules.billing.provider_spend import (
    ProviderReservationNotDispatchableError,
    ProviderSpendCoordinator,
    ProviderSpendRequest,
)
from app.modules.identity.models import Tenant

UNIT_PRICE_MICROS = 2000
FIRST_RESERVATION_MICROS = 4000
SECOND_RESERVATION_MICROS = 6000
EXPECTED_RESERVATION_COUNT = 2


@pytest.mark.asyncio
async def test_provider_spend_reserve_dispatch_settle_unknown_and_release():  # noqa: PLR0915
    test_url = make_url(settings.resolved_database_url).set(database="salesos_test")
    engine = create_async_engine(
        test_url,
        pool_pre_ping=True,
        connect_args={"command_timeout": 10},
    )
    async with engine.connect() as connection:
        outer = await connection.begin()
        assert await connection.scalar(text("SELECT current_database()")) == "salesos_test"
        tenant_id = uuid.uuid4()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            session.add(
                Tenant(
                    id=tenant_id,
                    name="Provider Spend Fixture",
                    slug=f"provider-spend-{uuid.uuid4()}",
                )
            )
            await session.flush()

            billing_scope = f"fixture-{uuid.uuid4()}"
            price_card_id = uuid.uuid4()
            account_budget_id = uuid.uuid4()
            tenant_budget_id = uuid.uuid4()
            period_start = datetime.now(UTC).date().replace(day=1)
            await connection.execute(
                text(
                    """
                    INSERT INTO provider_price_cards
                        (id, provider_key, operation_key, version, currency, unit_name,
                         max_unit_micros, effective_from, approval_reference, approved_by,
                         approved_at, enabled)
                    VALUES
                        (:id, 'scout', 'domain_lookup', 'fixture-v1', 'USD', 'lookup',
                         :unit_price, now() - interval '1 day',
                         'test fixture', 'test-owner', now(), true)
                    """
                ),
                {"id": price_card_id, "unit_price": UNIT_PRICE_MICROS},
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO provider_spend_limits
                        (id, provider_key, scope_type, scope_key, period_start, currency,
                         limit_micros, spent_micros, reserved_micros, enabled)
                    VALUES
                        (:account_id, 'scout', 'ACCOUNT', :billing_scope, :period_start,
                         'USD', 20000, 0, 0, true),
                        (:tenant_id, 'scout', 'TENANT', :tenant_scope, :period_start,
                         'USD', 10000, 0, 0, true)
                    """
                ),
                {
                    "account_id": account_budget_id,
                    "billing_scope": billing_scope,
                    "period_start": period_start,
                    "tenant_id": tenant_budget_id,
                    "tenant_scope": str(tenant_id),
                },
            )

            await connection.execute(text("SET LOCAL ROLE salesos_app"))
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            assert await connection.scalar(text("SELECT current_user")) == "salesos_app"
            assert not await connection.scalar(
                text("SELECT has_table_privilege(current_user, 'provider_spend_limits', 'UPDATE')")
            )
            assert not await connection.scalar(
                text(
                    "SELECT has_table_privilege(current_user, "
                    "'provider_spend_reservations', 'INSERT')"
                )
            )

            reservation_args = {
                "tenant_id": tenant_id,
                "provider_key": "scout",
                "operation_key": "domain_lookup",
                "billing_scope": billing_scope,
                "price_version": "fixture-v1",
                "units": 2,
                "idempotency_key": "fixture-request-1",
                "fingerprint": "a" * 64,
            }

            async def reserve(**overrides):
                values = {**reservation_args, **overrides}
                result = await connection.execute(
                    text(
                        """
                        SELECT * FROM reserve_provider_spend(
                            :tenant_id, :provider_key, :operation_key, :billing_scope,
                            :price_version, :units, :idempotency_key, :fingerprint
                        )
                        """
                    ),
                    values,
                )
                return result.mappings().one()

            first = await reserve()
            assert first["reservation_status"] == "RESERVED"
            assert first["reused"] is False
            assert first["estimated_micros"] == FIRST_RESERVATION_MICROS

            retry = await reserve()
            assert retry["reservation_id"] == first["reservation_id"]
            assert retry["reused"] is True

            with pytest.raises(Exception, match="different request"):
                async with connection.begin_nested():
                    await reserve(fingerprint="b" * 64)

            await connection.execute(
                text("SELECT mark_provider_spend_in_flight(:tenant_id, :reservation_id)"),
                {"tenant_id": tenant_id, "reservation_id": first["reservation_id"]},
            )
            settled = await connection.execute(
                text("SELECT * FROM settle_provider_spend(:tenant_id, :reservation_id, 3500)"),
                {"tenant_id": tenant_id, "reservation_id": first["reservation_id"]},
            )
            assert settled.mappings().one()["over_budget"] is False
            repeated_settlement = await connection.execute(
                text("SELECT * FROM settle_provider_spend(:tenant_id, :reservation_id, 3500)"),
                {"tenant_id": tenant_id, "reservation_id": first["reservation_id"]},
            )
            assert repeated_settlement.mappings().one()["over_budget"] is False

            second = await reserve(
                units=3,
                idempotency_key="fixture-request-2",
                fingerprint="c" * 64,
            )
            assert second["estimated_micros"] == SECOND_RESERVATION_MICROS
            await connection.execute(
                text("SELECT mark_provider_spend_in_flight(:tenant_id, :reservation_id)"),
                {"tenant_id": tenant_id, "reservation_id": second["reservation_id"]},
            )
            assert (
                await connection.scalar(
                    text("SELECT mark_provider_spend_unknown(:tenant_id, :reservation_id)"),
                    {"tenant_id": tenant_id, "reservation_id": second["reservation_id"]},
                )
                == "UNKNOWN"
            )

            with pytest.raises(Exception, match="budget exceeded"):
                async with connection.begin_nested():
                    await reserve(
                        units=1,
                        idempotency_key="fixture-request-3",
                        fingerprint="d" * 64,
                    )

            assert (
                await connection.scalar(
                    text("SELECT release_provider_spend(:tenant_id, :reservation_id, :reason)"),
                    {
                        "tenant_id": tenant_id,
                        "reservation_id": second["reservation_id"],
                        "reason": "Provider confirmed no charge.",
                    },
                )
                == "RELEASED"
            )

            visible_count = await connection.scalar(
                text(
                    "SELECT count(*) FROM provider_spend_reservations "
                    "WHERE tenant_id = :tenant_id"
                ),
                {"tenant_id": tenant_id},
            )
            assert visible_count == EXPECTED_RESERVATION_COUNT
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :other_tenant, true)"),
                {"other_tenant": str(uuid.uuid4())},
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM provider_spend_reservations"))
                == 0
            )
            with pytest.raises(Exception, match="tenant scope mismatch"):
                async with connection.begin_nested():
                    await reserve()
        finally:
            await session.close()
            if outer.is_active:
                await outer.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_provider_coordinator_commits_and_serializes_shared_account_limit():
    owner_url = make_url(settings.resolved_database_url).set(database="salesos_test")
    app_url = make_url(settings.app_database_url).set(database="salesos_test")
    owner_engine = create_async_engine(
        owner_url, pool_pre_ping=True, connect_args={"command_timeout": 10}
    )
    app_engine = create_async_engine(
        app_url, pool_pre_ping=True, connect_args={"command_timeout": 10}
    )
    tenant_id = uuid.uuid4()
    billing_scope = f"parallel-{uuid.uuid4()}"
    price_card_id = uuid.uuid4()
    account_budget_id = uuid.uuid4()
    tenant_budget_id = uuid.uuid4()
    price_version = f"parallel-{uuid.uuid4().hex[:12]}"
    period_start = datetime.now(UTC).date().replace(day=1)
    fixture_created = False
    try:
        async with owner_engine.connect() as connection:
            assert await connection.scalar(text("SELECT current_database()")) == "salesos_test"
        async with AsyncSession(owner_engine, expire_on_commit=False) as owner_session:
            owner_session.add(
                Tenant(
                    id=tenant_id,
                    name="Provider Spend Concurrent Fixture",
                    slug=f"provider-spend-concurrent-{uuid.uuid4()}",
                )
            )
            await owner_session.commit()
        async with owner_engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO provider_price_cards
                        (id, provider_key, operation_key, version, currency, unit_name,
                         max_unit_micros, effective_from, approval_reference, approved_by,
                         approved_at, enabled)
                    VALUES
                        (:id, 'scout', 'domain_lookup', :version, 'USD', 'lookup',
                         :unit_price, now() - interval '1 day',
                         'test fixture', 'test-owner', now(), true)
                    """
                ),
                {
                    "id": price_card_id,
                    "version": price_version,
                    "unit_price": UNIT_PRICE_MICROS,
                },
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO provider_spend_limits
                        (id, provider_key, scope_type, scope_key, period_start, currency,
                         limit_micros, spent_micros, reserved_micros, enabled)
                    VALUES
                        (:account_id, 'scout', 'ACCOUNT', :billing_scope, :period_start,
                         'USD', 6000, 0, 0, true),
                        (:tenant_budget_id, 'scout', 'TENANT', :tenant_scope, :period_start,
                         'USD', 20000, 0, 0, true)
                    """
                ),
                {
                    "account_id": account_budget_id,
                    "billing_scope": billing_scope,
                    "period_start": period_start,
                    "tenant_budget_id": tenant_budget_id,
                    "tenant_scope": str(tenant_id),
                },
            )
        fixture_created = True

        async with app_engine.connect() as connection:
            assert await connection.scalar(text("SELECT current_database()")) == "salesos_test"
            assert await connection.scalar(text("SELECT current_user")) == "salesos_app"
            assert await connection.scalar(
                text(
                    "SELECT NOT rolsuper AND NOT rolbypassrls "
                    "FROM pg_roles WHERE rolname = current_user"
                )
            ) is True

        coordinator = ProviderSpendCoordinator(
            async_sessionmaker(app_engine, expire_on_commit=False)
        )

        def request(
            key: str, fingerprint: str, *, units: int = 2
        ) -> ProviderSpendRequest:
            return ProviderSpendRequest(
                tenant_id=tenant_id,
                provider_key="scout",
                operation_key="domain_lookup",
                billing_scope_key=billing_scope,
                price_card_version=price_version,
                billable_units=units,
                idempotency_key=key,
                request_fingerprint=fingerprint * 64,
            )

        outcomes = await asyncio.gather(
            coordinator.reserve(request("parallel-request-a", "a")),
            coordinator.reserve(request("parallel-request-b", "b")),
            return_exceptions=True,
        )
        reservations = [item for item in outcomes if not isinstance(item, BaseException)]
        denials = [item for item in outcomes if isinstance(item, BaseException)]
        assert len(reservations) == 1
        assert len(denials) == 1
        assert reservations[0].status == "RESERVED"
        assert reservations[0].estimated_micros == FIRST_RESERVATION_MICROS

        winner_index = next(
            index for index, outcome in enumerate(outcomes) if not isinstance(outcome, BaseException)
        )
        winning_key = (
            "parallel-request-a" if winner_index == 0 else "parallel-request-b"
        )
        winning_fingerprint = "a" if winner_index == 0 else "b"
        with pytest.raises(ProviderReservationNotDispatchableError, match="already exists"):
            await coordinator.reserve(request(winning_key, winning_fingerprint))

        await coordinator.mark_in_flight(
            tenant_id=tenant_id, reservation_id=reservations[0].reservation_id
        )
        assert (
            await coordinator.settle(
                tenant_id=tenant_id,
                reservation_id=reservations[0].reservation_id,
                actual_micros=2500,
            )
            is False
        )
        assert (
            await coordinator.settle(
                tenant_id=tenant_id,
                reservation_id=reservations[0].reservation_id,
                actual_micros=2500,
            )
            is False
        )

        release_reservation = await coordinator.reserve(
            request("parallel-request-release", "c", units=1)
        )
        await coordinator.mark_in_flight(
            tenant_id=tenant_id, reservation_id=release_reservation.reservation_id
        )
        await coordinator.mark_unknown(
            tenant_id=tenant_id, reservation_id=release_reservation.reservation_id
        )
        await coordinator.release_confirmed_no_charge(
            tenant_id=tenant_id,
            reservation_id=release_reservation.reservation_id,
            reason="Provider confirmed the request was not billed.",
            provider_confirmed_no_charge=True,
        )

        async with owner_engine.connect() as connection:
            ledger = (
                await connection.execute(
                    text(
                        """
                        SELECT spent_micros, reserved_micros
                        FROM provider_spend_limits
                        WHERE id IN (:account_id, :tenant_budget_id)
                        ORDER BY scope_type
                        """
                    ),
                    {
                        "account_id": account_budget_id,
                        "tenant_budget_id": tenant_budget_id,
                    },
                )
            ).all()
            assert [row.reserved_micros for row in ledger] == [0, 0]
            assert [row.spent_micros for row in ledger] == [2500, 2500]
            states = dict(
                (
                    await connection.execute(
                        text(
                            "SELECT id, status FROM provider_spend_reservations "
                            "WHERE tenant_id = :tenant_id"
                        ),
                        {"tenant_id": tenant_id},
                    )
                ).all()
            )
            assert states[reservations[0].reservation_id] == "SETTLED"
            assert states[release_reservation.reservation_id] == "RELEASED"
    finally:
        if fixture_created:
            async with owner_engine.begin() as connection:
                await connection.execute(
                    text(
                        "DELETE FROM provider_spend_reservations WHERE tenant_id = :tenant_id"
                    ),
                    {"tenant_id": tenant_id},
                )
                await connection.execute(
                    text(
                        "DELETE FROM provider_spend_limits "
                        "WHERE id IN (:account_id, :tenant_budget_id)"
                    ),
                    {
                        "account_id": account_budget_id,
                        "tenant_budget_id": tenant_budget_id,
                    },
                )
                await connection.execute(
                    text("DELETE FROM provider_price_cards WHERE id = :price_card_id"),
                    {"price_card_id": price_card_id},
                )
                await connection.execute(
                    text("DELETE FROM tenants WHERE id = :tenant_id"),
                    {"tenant_id": tenant_id},
                )
        await app_engine.dispose()
        await owner_engine.dispose()
