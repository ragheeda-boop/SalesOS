"""STORY-06-01 — Plan.entitlements schema + tier defaults."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.admin.entitlements import (
    PlanEntitlements,
    default_entitlements_for_tier,
    domain_enabled,
    parse_entitlements,
)


def test_starter_packaging_matrix() -> None:
    e = default_entitlements_for_tier("starter")
    assert e.version == 1
    assert domain_enabled(e, "DOM-001") is True
    assert domain_enabled(e, "DOM-011") is False
    assert domain_enabled(e, "DOM-023") is False
    assert e.domains["DOM-021"].quota == 1
    assert e.domains["DOM-022"].mode == "limited"
    assert e.quotas.ai_tokens_monthly == 10_000
    assert e.quotas.seats == 5


def test_growth_enables_ai_and_gtm() -> None:
    e = default_entitlements_for_tier("growth")
    assert domain_enabled(e, "DOM-011") is True
    assert domain_enabled(e, "DOM-023") is True
    assert e.domains["DOM-021"].quota == 5
    assert e.domains["DOM-022"].mode == "full"
    assert e.quotas.ai_tokens_monthly == 500_000


def test_enterprise_unlimited_connectors_and_publish() -> None:
    e = default_entitlements_for_tier("enterprise")
    assert e.domains["DOM-021"].unlimited is True
    assert e.domains["DOM-024"].publish is True
    assert e.quotas.ai_tokens_unlimited is True
    assert e.support_sla == "dedicated_p0"


def test_parse_rejects_bad_domain_key() -> None:
    with pytest.raises(ValidationError):
        PlanEntitlements.model_validate(
            {"version": 1, "domains": {"CRM": {"enabled": True}}, "quotas": {}}
        )


def test_parse_empty_falls_back_free() -> None:
    e = parse_entitlements({})
    assert e.quotas.seats == 1
    assert domain_enabled(e, "DOM-011") is False
