"""STORY-05-02b — portal/invoice helpers + catalog fields (no real Stripe keys)."""

from __future__ import annotations

from app.modules.billing.stripe_invoice_sync import (
    map_stripe_invoice_status,
    stripe_amount_to_major,
)


def test_stripe_amount_to_major() -> None:
    assert stripe_amount_to_major(1050, "usd") == 10.5
    assert stripe_amount_to_major(0, "sar") == 0.0
    assert stripe_amount_to_major("bad", "usd") == 0.0


def test_map_invoice_status() -> None:
    assert map_stripe_invoice_status("paid") == "paid"
    assert map_stripe_invoice_status("open") == "open"
    assert map_stripe_invoice_status(None) == "open"


def test_plan_schema_accepts_stripe_price_ids() -> None:
    from app.modules.admin.schemas import PlanCreate, PlanTier

    body = PlanCreate(
        name="Growth",
        tier=PlanTier.GROWTH,
        stripe_price_id_monthly="price_test_fixture_not_live",
        stripe_price_id_yearly="price_test_fixture_yearly",
    )
    assert body.stripe_price_id_monthly.startswith("price_")


def test_require_stripe_secret_fail_closed(monkeypatch) -> None:
    from app.modules.billing import stripe_client

    monkeypatch.setattr(stripe_client.settings, "stripe_secret_key", "")
    try:
        stripe_client.require_stripe_secret()
        raise AssertionError("expected StripeNotConfiguredError")
    except stripe_client.StripeNotConfiguredError:
        pass
