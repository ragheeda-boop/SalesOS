"""STORY-06-03 — quota evaluation + path gates (pure)."""

from __future__ import annotations

from app.modules.admin.entitlements import default_entitlements_for_tier
from app.modules.admin.quota_enforcement import (
    evaluate_quota_violations,
    limits_from_entitlements,
    over_quota_payload,
)
from app.modules.admin.quota_gates import quota_metrics_for_path
from app.modules.billing.usage_metrics import METRIC_KEYS, normalize_op


def test_connectors_metric_is_gauge() -> None:
    assert "connectors" in METRIC_KEYS
    assert normalize_op(None, metric_key="connectors") == "set"


def test_quota_path_gates_cover_four_dimensions() -> None:
    assert "ai_tokens" in (quota_metrics_for_path("/api/v1/rag/ask", "POST") or ())
    assert "storage_mb" in (quota_metrics_for_path("/api/v1/ai/run", "GET") or ())
    assert "connectors" in (quota_metrics_for_path("/api/v1/integrations/x", "POST") or ())
    assert "seats" in (quota_metrics_for_path("/api/v1/identity/invite", "POST") or ())
    # Listing integrations must not hard-block on connector gauge.
    assert "connectors" not in (quota_metrics_for_path("/api/v1/integrations", "GET") or ())


def test_starter_limits_and_token_over_quota() -> None:
    ents = default_entitlements_for_tier("starter")
    limits = limits_from_entitlements(ents)
    assert limits["seats"].limit == 5
    assert limits["connectors"].limit == 1
    assert limits["ai_tokens"].limit == 10_000

    ok = evaluate_quota_violations(
        limits=limits,
        usage={"ai_tokens": 9999, "seats": 1, "connectors": 0, "storage_mb": 10},
        metrics=("ai_tokens",),
    )
    assert ok == []

    bad = evaluate_quota_violations(
        limits=limits,
        usage={"ai_tokens": 10_000, "seats": 1, "connectors": 0, "storage_mb": 10},
        metrics=("ai_tokens",),
    )
    assert len(bad) == 1
    assert bad[0].metric == "ai_tokens"
    assert bad[0].status_code == 429
    body = over_quota_payload(bad[0], period="2026-08")
    assert body["error"] == "quota_exceeded"
    assert body["metric"] == "ai_tokens"
    assert body["period"] == "2026-08"


def test_seat_and_connector_capacity() -> None:
    ents = default_entitlements_for_tier("starter")
    limits = limits_from_entitlements(ents)
    seat_hit = evaluate_quota_violations(
        limits=limits,
        usage={"seats": 5, "connectors": 0, "ai_tokens": 0, "storage_mb": 0},
        metrics=("seats",),
    )
    assert seat_hit and seat_hit[0].status_code == 403

    conn_hit = evaluate_quota_violations(
        limits=limits,
        usage={"seats": 1, "connectors": 1, "ai_tokens": 0, "storage_mb": 0},
        metrics=("connectors",),
    )
    assert conn_hit and conn_hit[0].metric == "connectors"


def test_enterprise_unlimited_tokens_and_connectors() -> None:
    ents = default_entitlements_for_tier("enterprise")
    limits = limits_from_entitlements(ents)
    assert limits["ai_tokens"].unlimited is True
    assert limits["connectors"].unlimited is True
    assert (
        evaluate_quota_violations(
            limits=limits,
            usage={"ai_tokens": 9e12, "connectors": 999, "seats": 1, "storage_mb": 1},
            metrics=("ai_tokens", "connectors"),
        )
        == []
    )


def test_storage_over_quota() -> None:
    ents = default_entitlements_for_tier("starter")
    limits = limits_from_entitlements(ents)
    hit = evaluate_quota_violations(
        limits=limits,
        usage={"storage_mb": 1000, "seats": 1, "connectors": 0, "ai_tokens": 0},
        metrics=("storage_mb",),
    )
    assert hit and hit[0].metric == "storage_mb" and hit[0].status_code == 403
