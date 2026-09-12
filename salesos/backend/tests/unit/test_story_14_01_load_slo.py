"""STORY-14-01 — Load/SLO harness unit tests (50-tenant companion)."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.load_slo.harness import MemLoadSloHarness
from app.modules.load_slo.remediation import build_remediation_plan
from app.modules.load_slo.simulator import (
    run_pooled_50_tenant_burst,
    run_pooled_50_tenant_sustained_sim,
)
from app.modules.load_slo.targets import (
    ERROR_RATE_MAX,
    LOAD_PROFILES,
    P95_LATENCY_MS_MAX,
    TARGET_TENANTS,
)


def test_feature_ai_copilot_remains_false() -> None:
    assert settings.feature_ai_copilot is False


def test_targets_match_50_tenant_checklist() -> None:
    assert TARGET_TENANTS == 50
    assert P95_LATENCY_MS_MAX == 500.0
    assert ERROR_RATE_MAX == 0.01


def test_burst_within_slo() -> None:
    out = run_pooled_50_tenant_burst()
    assert out.ok is True
    assert out.within_slo is True
    assert out.tenants == 50
    assert out.connection_pool_exhausted is False
    assert out.degradation_trend is False
    assert out.detail["live_traffic"] is False
    assert out.detail["prod_kill"] is False


def test_sustained_sim_within_slo() -> None:
    out = run_pooled_50_tenant_sustained_sim()
    assert out.ok is True
    assert out.within_slo is True
    assert out.detail["field_2h_soak"] is False


def test_p95_miss_emits_remediation() -> None:
    out = run_pooled_50_tenant_burst(p95_latency_ms=P95_LATENCY_MS_MAX + 50)
    assert out.within_slo is False
    plan = build_remediation_plan(out)
    assert plan["status"] == "needs_remediation"
    assert any("p95" in i.lower() for i in plan["items"])


def test_pool_exhaustion_miss() -> None:
    out = run_pooled_50_tenant_burst(connection_pool_exhausted=True)
    assert out.ok is False
    plan = build_remediation_plan(out)
    assert plan["status"] == "needs_remediation"
    assert any("pool" in i.lower() for i in plan["items"])


def test_degradation_trend_miss() -> None:
    out = run_pooled_50_tenant_sustained_sim(degradation_trend=True)
    assert out.ok is False
    plan = build_remediation_plan(out)
    assert any("degradation" in i.lower() for i in plan["items"])


def test_harness_run_all_writes_postmortems() -> None:
    harness = MemLoadSloHarness()
    reports = harness.run_all()
    assert len(reports) == len(LOAD_PROFILES)
    assert all(r.ok for r in reports)
    assert {r.profile for r in reports} == set(LOAD_PROFILES)
    pms = harness.list_postmortems()
    assert len(pms) == 2
    assert all(p.outcome == "within_slo" for p in pms)
    rem = harness.latest_remediation()
    assert rem["status"] == "held"


def test_unknown_profile_rejected() -> None:
    harness = MemLoadSloHarness()
    with pytest.raises(ValueError, match="unknown profile"):
        harness.run("prod_kill")
