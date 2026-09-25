"""Add durable provider price cards, spend limits, and atomic reservations.

Revision ID: t3u4v5w6x7
Revises: s2t3u4v5w6x7
"""

# SQL function bodies below are kept as SQL for safe review and execution.
# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "t3u4v5w6x7"
down_revision: str | None = "s2t3u4v5w6x7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RESERVATION_TABLE = "provider_spend_reservations"


def _function(sql: str) -> None:
    op.execute(sa.text(sql))


def _grant_app_function(signature: str) -> None:
    op.execute(
        sa.text(
            """
            DO $grant$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN
                    EXECUTE 'GRANT EXECUTE ON FUNCTION """
            + signature
            + """ TO salesos_app';
                END IF;
            END
            $grant$;
            """
        )
    )


def upgrade() -> None:
    op.create_table(
        "provider_price_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_key", sa.String(64), nullable=False),
        sa.Column("operation_key", sa.String(64), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("unit_name", sa.String(64), nullable=False),
        sa.Column("max_unit_micros", sa.BigInteger(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("approval_reference", sa.String(255), nullable=False),
        sa.Column("approved_by", sa.String(128), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "provider_key", "operation_key", "version", name="uq_provider_price_card_version"
        ),
        sa.CheckConstraint("max_unit_micros >= 0", name="ck_provider_price_card_nonnegative"),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_provider_price_card_currency"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="ck_provider_price_card_dates",
        ),
    )
    op.create_index(
        "ix_provider_price_cards_active",
        "provider_price_cards",
        ["provider_key", "operation_key", "enabled", "effective_from"],
    )

    op.create_table(
        "provider_spend_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_key", sa.String(64), nullable=False),
        sa.Column("scope_type", sa.String(16), nullable=False),
        sa.Column("scope_key", sa.String(128), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("limit_micros", sa.BigInteger(), nullable=False),
        sa.Column("spent_micros", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reserved_micros", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "provider_key",
            "scope_type",
            "scope_key",
            "period_start",
            name="uq_provider_spend_limit_scope_period",
        ),
        sa.CheckConstraint("scope_type IN ('ACCOUNT', 'TENANT')", name="ck_provider_spend_scope"),
        sa.CheckConstraint("limit_micros >= 0", name="ck_provider_spend_limit_nonnegative"),
        sa.CheckConstraint("spent_micros >= 0", name="ck_provider_spend_spent_nonnegative"),
        sa.CheckConstraint("reserved_micros >= 0", name="ck_provider_spend_reserved_nonnegative"),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_provider_spend_currency"),
    )

    op.create_table(
        _RESERVATION_TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_key", sa.String(64), nullable=False),
        sa.Column("operation_key", sa.String(64), nullable=False),
        sa.Column("billing_scope_key", sa.String(128), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("price_card_version", sa.String(64), nullable=False),
        sa.Column("billable_units", sa.BigInteger(), nullable=False),
        sa.Column("estimated_micros", sa.BigInteger(), nullable=False),
        sa.Column("actual_micros", sa.BigInteger()),
        sa.Column("status", sa.String(16), nullable=False, server_default="RESERVED"),
        sa.Column("resolution_reason", sa.String(240)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("settled_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "tenant_id", "provider_key", "idempotency_key", name="uq_provider_spend_idempotency"
        ),
        sa.CheckConstraint(
            "status IN ('RESERVED', 'IN_FLIGHT', 'UNKNOWN', 'SETTLED', 'RELEASED')",
            name="ck_provider_spend_reservation_status",
        ),
        sa.CheckConstraint("billable_units > 0", name="ck_provider_spend_units_positive"),
        sa.CheckConstraint("estimated_micros >= 0", name="ck_provider_spend_estimate_nonnegative"),
        sa.CheckConstraint(
            "actual_micros IS NULL OR actual_micros >= 0",
            name="ck_provider_spend_actual_nonnegative",
        ),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'", name="ck_provider_spend_reservation_currency"
        ),
    )
    op.create_index(
        "ix_provider_spend_reservations_tenant_period",
        _RESERVATION_TABLE,
        ["tenant_id", "period_start", "provider_key"],
    )
    op.create_index(
        "ix_provider_spend_reservations_reconcile",
        _RESERVATION_TABLE,
        ["status", "updated_at"],
        postgresql_where=sa.text("status IN ('IN_FLIGHT', 'UNKNOWN')"),
    )

    for statement in generate_policy_sql(_RESERVATION_TABLE).strip().split(";\n"):
        if statement.strip():
            op.execute(sa.text(statement))

    # Provider call lifecycle and atomic budget reservation. These functions
    # are the only runtime write path; direct shared-budget/config access is
    # intentionally unavailable to the application role.
    _function(
        r"""
        CREATE OR REPLACE FUNCTION reserve_provider_spend(
            p_tenant_id uuid,
            p_provider_key text,
            p_operation_key text,
            p_billing_scope_key text,
            p_price_card_version text,
            p_billable_units bigint,
            p_idempotency_key text,
            p_request_fingerprint text
        ) RETURNS TABLE (
            reservation_id uuid,
            reservation_status text,
            reused boolean,
            estimated_micros bigint,
            currency character(3)
        )
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $body$
        DECLARE
            v_period date := date_trunc('month', now() AT TIME ZONE 'UTC')::date;
            v_existing provider_spend_reservations%ROWTYPE;
            v_account provider_spend_limits%ROWTYPE;
            v_tenant provider_spend_limits%ROWTYPE;
            v_card provider_price_cards%ROWTYPE;
            v_amount bigint;
            v_id uuid;
        BEGIN
            IF current_setting('app.tenant_id', true) IS DISTINCT FROM p_tenant_id::text THEN
                RAISE EXCEPTION 'tenant scope mismatch' USING ERRCODE = '42501';
            END IF;
            IF p_billable_units IS NULL OR p_billable_units <= 0
               OR p_provider_key IS NULL OR p_provider_key !~ '^[a-z][a-z0-9_]{1,63}$'
               OR p_operation_key IS NULL OR p_operation_key !~ '^[a-z][a-z0-9_]{1,63}$'
               OR p_billing_scope_key IS NULL
               OR p_billing_scope_key !~ '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'
               OR p_idempotency_key IS NULL
               OR length(btrim(p_idempotency_key)) NOT BETWEEN 1 AND 128
               OR p_idempotency_key ~ '[[:cntrl:]]'
               OR p_request_fingerprint IS NULL
               OR p_request_fingerprint !~ '^[0-9a-f]{64}$' THEN
                RAISE EXCEPTION 'invalid provider reservation request' USING ERRCODE = '22023';
            END IF;

            SELECT * INTO v_existing
            FROM provider_spend_reservations r
            WHERE r.tenant_id = p_tenant_id
              AND r.provider_key = p_provider_key
              AND r.idempotency_key = p_idempotency_key
            FOR UPDATE;
            IF FOUND THEN
                IF v_existing.request_fingerprint <> p_request_fingerprint THEN
                    RAISE EXCEPTION 'idempotency key reused with a different request'
                        USING ERRCODE = '22023';
                END IF;
                RETURN QUERY SELECT v_existing.id, v_existing.status::text, true,
                                    v_existing.estimated_micros, v_existing.currency;
                RETURN;
            END IF;

            -- Lock order is shared billing account, then tenant. Every caller
            -- uses this order so concurrent reservations cannot overspend or deadlock.
            SELECT * INTO v_account
            FROM provider_spend_limits b
            WHERE b.provider_key = p_provider_key
              AND b.scope_type = 'ACCOUNT'
              AND b.scope_key = p_billing_scope_key
              AND b.period_start = v_period
            FOR UPDATE;
            IF NOT FOUND OR NOT v_account.enabled THEN
                RAISE EXCEPTION 'provider account budget is not enabled' USING ERRCODE = 'P0001';
            END IF;

            SELECT * INTO v_tenant
            FROM provider_spend_limits b
            WHERE b.provider_key = p_provider_key
              AND b.scope_type = 'TENANT'
              AND b.scope_key = p_tenant_id::text
              AND b.period_start = v_period
            FOR UPDATE;
            IF NOT FOUND OR NOT v_tenant.enabled THEN
                RAISE EXCEPTION 'provider tenant budget is not enabled' USING ERRCODE = 'P0001';
            END IF;

            -- Recheck after the budget locks: a parallel request with this
            -- idempotency key may have committed while this transaction waited.
            SELECT * INTO v_existing
            FROM provider_spend_reservations r
            WHERE r.tenant_id = p_tenant_id
              AND r.provider_key = p_provider_key
              AND r.idempotency_key = p_idempotency_key
            FOR UPDATE;
            IF FOUND THEN
                IF v_existing.request_fingerprint <> p_request_fingerprint THEN
                    RAISE EXCEPTION 'idempotency key reused with a different request'
                        USING ERRCODE = '22023';
                END IF;
                RETURN QUERY SELECT v_existing.id, v_existing.status::text, true,
                                    v_existing.estimated_micros, v_existing.currency;
                RETURN;
            END IF;

            SELECT * INTO v_card
            FROM provider_price_cards c
            WHERE c.provider_key = p_provider_key
              AND c.operation_key = p_operation_key
              AND c.version = p_price_card_version
              AND c.enabled
              AND c.effective_from <= now()
              AND (c.effective_to IS NULL OR c.effective_to > now());
            IF NOT FOUND THEN
                RAISE EXCEPTION 'approved provider price card is not active' USING ERRCODE = 'P0001';
            END IF;
            IF v_account.currency <> v_card.currency OR v_tenant.currency <> v_card.currency THEN
                RAISE EXCEPTION 'provider budget currency does not match active price card'
                    USING ERRCODE = 'P0001';
            END IF;
            IF v_card.max_unit_micros > 0
               AND p_billable_units > 9223372036854775807 / v_card.max_unit_micros THEN
                RAISE EXCEPTION 'provider cost estimate overflow' USING ERRCODE = '22003';
            END IF;
            v_amount := v_card.max_unit_micros * p_billable_units;
            IF v_account.spent_micros + v_account.reserved_micros + v_amount > v_account.limit_micros
               OR v_tenant.spent_micros + v_tenant.reserved_micros + v_amount > v_tenant.limit_micros THEN
                RAISE EXCEPTION 'provider spend budget exceeded' USING ERRCODE = 'P0001';
            END IF;

            UPDATE provider_spend_limits
            SET reserved_micros = reserved_micros + v_amount, updated_at = now()
            WHERE id IN (v_account.id, v_tenant.id);

            v_id := gen_random_uuid();
            INSERT INTO provider_spend_reservations (
                id, tenant_id, provider_key, operation_key, billing_scope_key,
                period_start, currency, idempotency_key, request_fingerprint,
                price_card_version, billable_units, estimated_micros, status
            ) VALUES (
                v_id, p_tenant_id, p_provider_key, p_operation_key, p_billing_scope_key,
                v_period, v_card.currency, p_idempotency_key, p_request_fingerprint,
                p_price_card_version, p_billable_units, v_amount, 'RESERVED'
            );

            RETURN QUERY SELECT v_id, 'RESERVED'::text, false, v_amount, v_card.currency;
        END
        $body$;
        """
    )
    _function(
        r"""
        CREATE OR REPLACE FUNCTION mark_provider_spend_in_flight(
            p_tenant_id uuid, p_reservation_id uuid
        ) RETURNS text
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $body$
        DECLARE v_status text;
        BEGIN
            IF current_setting('app.tenant_id', true) IS DISTINCT FROM p_tenant_id::text THEN
                RAISE EXCEPTION 'tenant scope mismatch' USING ERRCODE = '42501';
            END IF;
            UPDATE provider_spend_reservations
            SET status = 'IN_FLIGHT', updated_at = now()
            WHERE id = p_reservation_id AND tenant_id = p_tenant_id AND status = 'RESERVED'
            RETURNING status INTO v_status;
            IF FOUND THEN RETURN v_status; END IF;
            SELECT status INTO v_status FROM provider_spend_reservations
            WHERE id = p_reservation_id AND tenant_id = p_tenant_id;
            IF v_status IS NULL THEN
                RAISE EXCEPTION 'provider reservation not found' USING ERRCODE = 'P0002';
            END IF;
            RAISE EXCEPTION 'provider reservation is already %', v_status USING ERRCODE = 'P0001';
        END
        $body$;
        """
    )
    _function(
        r"""
        CREATE OR REPLACE FUNCTION mark_provider_spend_unknown(
            p_tenant_id uuid, p_reservation_id uuid
        ) RETURNS text
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $body$
        DECLARE v_status text;
        BEGIN
            IF current_setting('app.tenant_id', true) IS DISTINCT FROM p_tenant_id::text THEN
                RAISE EXCEPTION 'tenant scope mismatch' USING ERRCODE = '42501';
            END IF;
            UPDATE provider_spend_reservations
            SET status = 'UNKNOWN', updated_at = now()
            WHERE id = p_reservation_id AND tenant_id = p_tenant_id AND status = 'IN_FLIGHT'
            RETURNING status INTO v_status;
            IF FOUND THEN RETURN v_status; END IF;
            SELECT status INTO v_status FROM provider_spend_reservations
            WHERE id = p_reservation_id AND tenant_id = p_tenant_id;
            IF v_status = 'UNKNOWN' THEN RETURN v_status; END IF;
            IF v_status IS NULL THEN
                RAISE EXCEPTION 'provider reservation not found' USING ERRCODE = 'P0002';
            END IF;
            RAISE EXCEPTION 'provider reservation cannot become unknown from %', v_status
                USING ERRCODE = 'P0001';
        END
        $body$;
        """
    )
    _function(
        r"""
        CREATE OR REPLACE FUNCTION settle_provider_spend(
            p_tenant_id uuid, p_reservation_id uuid, p_actual_micros bigint
        ) RETURNS TABLE (over_budget boolean)
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $body$
        DECLARE
            v_res provider_spend_reservations%ROWTYPE;
            v_account provider_spend_limits%ROWTYPE;
            v_tenant provider_spend_limits%ROWTYPE;
        BEGIN
            IF current_setting('app.tenant_id', true) IS DISTINCT FROM p_tenant_id::text THEN
                RAISE EXCEPTION 'tenant scope mismatch' USING ERRCODE = '42501';
            END IF;
            IF p_actual_micros IS NULL OR p_actual_micros < 0 THEN
                RAISE EXCEPTION 'actual cost must be non-negative' USING ERRCODE = '22023';
            END IF;
            SELECT * INTO v_res FROM provider_spend_reservations r
            WHERE r.id = p_reservation_id AND r.tenant_id = p_tenant_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'provider reservation not found' USING ERRCODE = 'P0002';
            END IF;
            SELECT * INTO v_account FROM provider_spend_limits b
            WHERE b.provider_key = v_res.provider_key AND b.scope_type = 'ACCOUNT'
              AND b.scope_key = v_res.billing_scope_key AND b.period_start = v_res.period_start
            FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'provider account budget missing' USING ERRCODE = 'P0001'; END IF;
            SELECT * INTO v_tenant FROM provider_spend_limits b
            WHERE b.provider_key = v_res.provider_key AND b.scope_type = 'TENANT'
              AND b.scope_key = p_tenant_id::text AND b.period_start = v_res.period_start
            FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'provider tenant budget missing' USING ERRCODE = 'P0001'; END IF;
            IF v_res.status = 'SETTLED' THEN
                IF v_res.actual_micros <> p_actual_micros THEN
                    RAISE EXCEPTION 'settled provider cost cannot be changed' USING ERRCODE = '22023';
                END IF;
            ELSIF v_res.status NOT IN ('IN_FLIGHT', 'UNKNOWN') THEN
                RAISE EXCEPTION 'provider reservation cannot settle from %', v_res.status
                    USING ERRCODE = 'P0001';
            ELSE
                IF v_account.reserved_micros < v_res.estimated_micros
                   OR v_tenant.reserved_micros < v_res.estimated_micros THEN
                    RAISE EXCEPTION 'provider reservation ledger is inconsistent' USING ERRCODE = 'P0001';
                END IF;
                UPDATE provider_spend_limits
                SET reserved_micros = reserved_micros - v_res.estimated_micros,
                    spent_micros = spent_micros + p_actual_micros,
                    updated_at = now()
                WHERE id IN (v_account.id, v_tenant.id);
                UPDATE provider_spend_reservations
                SET actual_micros = p_actual_micros, status = 'SETTLED',
                    settled_at = now(), updated_at = now()
                WHERE id = p_reservation_id;
                v_account.reserved_micros := v_account.reserved_micros - v_res.estimated_micros;
                v_tenant.reserved_micros := v_tenant.reserved_micros - v_res.estimated_micros;
                v_account.spent_micros := v_account.spent_micros + p_actual_micros;
                v_tenant.spent_micros := v_tenant.spent_micros + p_actual_micros;
            END IF;
            RETURN QUERY SELECT
                v_account.spent_micros + v_account.reserved_micros > v_account.limit_micros
                OR v_tenant.spent_micros + v_tenant.reserved_micros > v_tenant.limit_micros;
        END
        $body$;
        """
    )
    _function(
        r"""
        CREATE OR REPLACE FUNCTION release_provider_spend(
            p_tenant_id uuid, p_reservation_id uuid, p_reason text
        ) RETURNS text
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $body$
        DECLARE
            v_res provider_spend_reservations%ROWTYPE;
            v_account provider_spend_limits%ROWTYPE;
            v_tenant provider_spend_limits%ROWTYPE;
        BEGIN
            IF current_setting('app.tenant_id', true) IS DISTINCT FROM p_tenant_id::text THEN
                RAISE EXCEPTION 'tenant scope mismatch' USING ERRCODE = '42501';
            END IF;
            IF p_reason IS NULL OR length(btrim(p_reason)) NOT BETWEEN 8 AND 240 THEN
                RAISE EXCEPTION 'release reason must be 8 to 240 characters' USING ERRCODE = '22023';
            END IF;
            SELECT * INTO v_res FROM provider_spend_reservations r
            WHERE r.id = p_reservation_id AND r.tenant_id = p_tenant_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'provider reservation not found' USING ERRCODE = 'P0002';
            END IF;
            IF v_res.status = 'RELEASED' THEN RETURN v_res.status; END IF;
            IF v_res.status NOT IN ('RESERVED', 'IN_FLIGHT', 'UNKNOWN') THEN
                RAISE EXCEPTION 'provider reservation cannot release from %', v_res.status
                    USING ERRCODE = 'P0001';
            END IF;
            SELECT * INTO v_account FROM provider_spend_limits b
            WHERE b.provider_key = v_res.provider_key AND b.scope_type = 'ACCOUNT'
              AND b.scope_key = v_res.billing_scope_key AND b.period_start = v_res.period_start
            FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'provider account budget missing' USING ERRCODE = 'P0001'; END IF;
            SELECT * INTO v_tenant FROM provider_spend_limits b
            WHERE b.provider_key = v_res.provider_key AND b.scope_type = 'TENANT'
              AND b.scope_key = p_tenant_id::text AND b.period_start = v_res.period_start
            FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'provider tenant budget missing' USING ERRCODE = 'P0001'; END IF;
            IF v_account.reserved_micros < v_res.estimated_micros
               OR v_tenant.reserved_micros < v_res.estimated_micros THEN
                RAISE EXCEPTION 'provider reservation ledger is inconsistent' USING ERRCODE = 'P0001';
            END IF;
            UPDATE provider_spend_limits
            SET reserved_micros = reserved_micros - v_res.estimated_micros, updated_at = now()
            WHERE id IN (v_account.id, v_tenant.id);
            UPDATE provider_spend_reservations
            SET status = 'RELEASED', resolution_reason = btrim(p_reason), updated_at = now()
            WHERE id = p_reservation_id;
            RETURN 'RELEASED';
        END
        $body$;
        """
    )

    function_signatures = (
        "reserve_provider_spend(uuid, text, text, text, text, bigint, text, text)",
        "mark_provider_spend_in_flight(uuid, uuid)",
        "mark_provider_spend_unknown(uuid, uuid)",
        "settle_provider_spend(uuid, uuid, bigint)",
        "release_provider_spend(uuid, uuid, text)",
    )
    for signature in function_signatures:
        _function("REVOKE ALL ON FUNCTION " + signature + " FROM PUBLIC")
        _grant_app_function(signature)

    op.execute(sa.text("REVOKE ALL ON provider_price_cards FROM PUBLIC"))
    op.execute(sa.text("REVOKE ALL ON provider_spend_limits FROM PUBLIC"))
    op.execute(sa.text("REVOKE ALL ON provider_spend_reservations FROM PUBLIC"))
    op.execute(
        sa.text(
            """
            DO $revoke$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN
                    EXECUTE 'REVOKE ALL ON provider_price_cards FROM salesos_app';
                    EXECUTE 'REVOKE ALL ON provider_spend_limits FROM salesos_app';
                    EXECUTE 'GRANT SELECT ON provider_spend_reservations TO salesos_app';
                    EXECUTE 'REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER '
                        'ON provider_spend_reservations FROM salesos_app';
                END IF;
            END
            $revoke$;
            """
        )
    )


def downgrade() -> None:
    function_signatures = (
        "release_provider_spend(uuid, uuid, text)",
        "settle_provider_spend(uuid, uuid, bigint)",
        "mark_provider_spend_unknown(uuid, uuid)",
        "mark_provider_spend_in_flight(uuid, uuid)",
        "reserve_provider_spend(uuid, text, text, text, text, bigint, text, text)",
    )
    for signature in function_signatures:
        _function("DROP FUNCTION " + signature)
    op.execute(
        sa.text(
            'DROP POLICY IF EXISTS "tenant_isolation_provider_spend_reservations" '
            "ON provider_spend_reservations"
        )
    )
    op.execute(sa.text("ALTER TABLE provider_spend_reservations NO FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE provider_spend_reservations DISABLE ROW LEVEL SECURITY"))
    op.drop_index("ix_provider_spend_reservations_reconcile", table_name=_RESERVATION_TABLE)
    op.drop_index("ix_provider_spend_reservations_tenant_period", table_name=_RESERVATION_TABLE)
    op.drop_table(_RESERVATION_TABLE)
    op.drop_index("ix_provider_price_cards_active", table_name="provider_price_cards")
    op.drop_table("provider_spend_limits")
    op.drop_table("provider_price_cards")
