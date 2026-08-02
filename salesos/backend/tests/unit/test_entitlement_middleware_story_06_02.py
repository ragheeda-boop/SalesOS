"""STORY-06-02 — entitlement path gates + domain checks (pure)."""

from __future__ import annotations

from app.modules.admin.entitlement_gates import (
    path_skips_entitlement_guard,
    required_domain_for_path,
)
from app.modules.admin.entitlements import (
    default_entitlements_for_tier,
    domain_enabled,
)


def test_three_dom_path_gates() -> None:
    assert required_domain_for_path("/api/v1/rag/ask").domain == "DOM-011"
    assert required_domain_for_path("/api/v1/ai/generate").domain == "DOM-011"
    assert required_domain_for_path("/api/v1/copilot/query").domain == "DOM-012"
    assert required_domain_for_path("/api/v1/signals/feed").domain == "DOM-023"
    assert required_domain_for_path("/api/v1/integrations/google/sync").domain == "DOM-021"


def test_ungated_and_skip_paths() -> None:
    assert required_domain_for_path("/api/v1/contacts") is None
    assert path_skips_entitlement_guard("/api/v1/admin/plans") is True
    assert path_skips_entitlement_guard("/api/v1/auth/login") is True


def test_owner_admin_auth_identity_skipped() -> None:
    """CI safety: Owner/admin/auth must never be entitlement-gated."""
    for path in (
        "/api/v1/admin/tenants",
        "/api/v1/admin/billing/catalog",
        "/api/v1/admin/billing/stripe/status",
        "/api/v1/auth/login",
        "/api/v1/owner/me",
        "/api/v1/identity/users",
        "/api/v1/billing/stripe/webhook",
        "/health",
    ):
        assert path_skips_entitlement_guard(path) is True


def test_starter_blocks_three_combinations() -> None:
    e = default_entitlements_for_tier("starter")
    assert domain_enabled(e, "DOM-011") is False
    assert domain_enabled(e, "DOM-012") is False
    assert domain_enabled(e, "DOM-023") is False
    # Integration hub entitled with quota on starter
    assert domain_enabled(e, "DOM-021") is True


def test_growth_allows_ai_gtm_and_integrations() -> None:
    e = default_entitlements_for_tier("growth")
    assert domain_enabled(e, "DOM-011") is True
    assert domain_enabled(e, "DOM-012") is True
    assert domain_enabled(e, "DOM-023") is True
    assert domain_enabled(e, "DOM-021") is True
