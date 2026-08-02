"""STORY-06-04 — Security adversarial entitlement / quota bypass suite.

Covers plan × gated-capability matrix, server-side entitlement denial,
quota_exceeded contracts, cross-tenant isolation, Owner/admin skip,
enforcement flags off, and common abuse/path tricks.

Does not weaken auth/CSRF/RBAC/tenant isolation. DEC-085 untouched.
Not Production GO.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.modules.admin.entitlement_gates import (
    path_skips_entitlement_guard,
    required_domain_for_path,
)
from app.modules.admin.entitlement_middleware import EntitlementEnforcementMiddleware
from app.modules.admin.entitlements import (
    default_entitlements_for_tier,
    domain_enabled,
)
from app.modules.admin.quota_enforcement import (
    evaluate_quota_violations,
    limits_from_entitlements,
    over_quota_payload,
)
from app.modules.admin.quota_gates import quota_metrics_for_path

# Gated commercial path family × DOM (middleware registry).
_GATED_PATHS: tuple[tuple[str, str], ...] = (
    ("/api/v1/rag/ask", "DOM-011"),
    ("/api/v1/ai/generate", "DOM-011"),
    ("/api/v1/copilot/query", "DOM-012"),
    ("/api/v1/signals/feed", "DOM-023"),
    ("/api/v1/integrations/sync", "DOM-021"),
)

# COMMERCIAL_LAUNCH_PLAN §2 + default_entitlements_for_tier.
_DOMAIN_MATRIX: dict[str, dict[str, bool]] = {
    "free": {
        "DOM-011": False,
        "DOM-012": False,
        "DOM-023": False,
        "DOM-021": False,
    },
    "starter": {
        "DOM-011": False,
        "DOM-012": False,
        "DOM-023": False,
        "DOM-021": True,
    },
    "growth": {
        "DOM-011": True,
        "DOM-012": True,
        "DOM-023": True,
        "DOM-021": True,
    },
    "enterprise": {
        "DOM-011": True,
        "DOM-012": True,
        "DOM-023": True,
        "DOM-021": True,
    },
}

_OWNER_ADMIN_SKIP: tuple[str, ...] = (
    "/api/v1/admin/tenants",
    "/api/v1/admin/billing/catalog",
    "/api/v1/admin/plans",
    "/api/v1/auth/login",
    "/api/v1/owner/me",
    "/api/v1/identity/users",
    "/api/v1/billing/stripe/webhook",
    "/health",
)

_TENANT_A = "11111111-1111-1111-1111-111111111111"
_TENANT_B = "22222222-2222-2222-2222-222222222222"


def test_plan_capability_matrix_denies_and_allows() -> None:
    """Full plan × gated DOM matrix — zero entitlement-bypass cells."""
    for tier, expected in _DOMAIN_MATRIX.items():
        ents = default_entitlements_for_tier(tier)
        for domain, allow in expected.items():
            assert domain_enabled(ents, domain) is allow, f"{tier}/{domain}"
        for path, domain in _GATED_PATHS:
            gate = required_domain_for_path(path)
            assert gate is not None and gate.domain == domain
            assert domain_enabled(ents, gate.domain) is expected[domain]


def test_owner_admin_auth_never_domain_gated() -> None:
    for path in _OWNER_ADMIN_SKIP:
        assert path_skips_entitlement_guard(path) is True
        assert required_domain_for_path(path) is None


def test_abuse_path_traversal_cannot_reach_admin_skip() -> None:
    """`..` under a gated prefix must not inherit Owner/admin skip."""
    sneaky = "/api/v1/rag/../admin/tenants"
    assert path_skips_entitlement_guard(sneaky) is False
    gate = required_domain_for_path(sneaky)
    assert gate is not None
    assert gate.domain == "DOM-011"


def test_abuse_query_string_still_gates() -> None:
    gate = required_domain_for_path("/api/v1/copilot/query?upgrade=true")
    assert gate is not None and gate.domain == "DOM-012"
    assert path_skips_entitlement_guard("/api/v1/admin/tenants?x=1") is True


def test_seat_quota_still_applies_on_identity_invite() -> None:
    """Identity is domain-skipped; seat burn on invite must still quota-gate."""
    assert path_skips_entitlement_guard("/api/v1/identity/invite") is True
    assert "seats" in (quota_metrics_for_path("/api/v1/identity/invite", "POST") or ())


@pytest.mark.parametrize(
    "metric,usage_key,status",
    [
        ("seats", "seats", 403),
        ("connectors", "connectors", 403),
        ("storage_mb", "storage_mb", 403),
        ("ai_tokens", "ai_tokens", 429),
    ],
)
def test_quota_exceeded_contract_per_metric(metric: str, usage_key: str, status: int) -> None:
    ents = default_entitlements_for_tier("starter")
    limits = limits_from_entitlements(ents)
    lim = limits[metric]
    used = float(lim.limit) if lim.limit > 0 else 1.0
    usage = {
        "seats": 0.0,
        "connectors": 0.0,
        "storage_mb": 0.0,
        "ai_tokens": 0.0,
        usage_key: used,
    }
    hits = evaluate_quota_violations(limits=limits, usage=usage, metrics=(metric,))
    assert len(hits) == 1
    assert hits[0].status_code == status
    body = over_quota_payload(hits[0], period="2026-08", tier="starter")
    assert body["error"] == "quota_exceeded"
    assert body["metric"] == metric


def test_cross_tenant_entitlement_isolation_pure() -> None:
    """Starter vs Growth packages must not collapse — different deny sets."""
    a = default_entitlements_for_tier("starter")
    b = default_entitlements_for_tier("growth")
    assert domain_enabled(a, "DOM-011") is False
    assert domain_enabled(b, "DOM-011") is True
    assert domain_enabled(a, "DOM-023") is False
    assert domain_enabled(b, "DOM-023") is True


# --- ASGI middleware adversarial harness ---------------------------------


def _session_factory():
    @asynccontextmanager
    async def _cm():
        yield MagicMock()

    return _cm


def _make_entitlement_app() -> FastAPI:
    app = FastAPI()

    async def ok() -> JSONResponse:
        return JSONResponse({"ok": True})

    for path, _ in _GATED_PATHS:
        app.add_api_route(path, ok, methods=["GET", "POST"])
    app.add_api_route("/api/v1/identity/invite", ok, methods=["POST"])
    app.add_api_route("/api/v1/admin/tenants", ok, methods=["GET", "POST"])
    app.add_api_route("/api/v1/auth/login", ok, methods=["POST"])
    app.add_api_route("/api/v1/owner/me", ok, methods=["GET"])
    app.add_api_route("/api/v1/contacts", ok, methods=["GET"])
    app.add_api_route("/health", ok, methods=["GET"])

    app.add_middleware(EntitlementEnforcementMiddleware)
    app.state.db_session_factory = _session_factory()
    return app


async def _request(
    app: FastAPI,
    method: str,
    path: str,
    *,
    tenant_id: str | None,
    headers: dict[str, str] | None = None,
) -> Any:
    hdrs = dict(headers or {})
    if tenant_id:
        hdrs["X-Tenant-Id"] = tenant_id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, headers=hdrs)


@pytest.mark.asyncio
async def test_middleware_starter_denied_growth_allowed_matrix() -> None:
    """Direct API calls: Starter denied on AI/GTM; Growth allowed (server-side)."""
    app = _make_entitlement_app()

    async def resolve_for_tier(db: Any, tenant_id: str) -> tuple[Any, dict[str, Any]]:
        tier = "starter" if tenant_id == _TENANT_A else "growth"
        return default_entitlements_for_tier(tier), {
            "plan_id": f"plan-{tier}",
            "tier": tier,
            "source": "test",
        }

    usage = {
        "usage": {
            "seats": 1.0,
            "connectors": 0.0,
            "ai_tokens": 0.0,
            "storage_mb": 10.0,
        },
        "period": "2026-08",
    }

    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(side_effect=resolve_for_tier),
        ),
        patch("app.modules.admin.entitlement_middleware.UsageMeterService") as meter_cls,
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        meter_cls.return_value.quota_usage_snapshot = AsyncMock(return_value=usage)

        for path, domain in _GATED_PATHS:
            if domain == "DOM-021":
                # Starter entitled for integrations (quota separate).
                r_a = await _request(app, "GET", path, tenant_id=_TENANT_A)
                assert r_a.status_code == 200, path
            else:
                r_a = await _request(app, "GET", path, tenant_id=_TENANT_A)
                assert r_a.status_code == 403, path
                body = r_a.json()
                assert domain in body.get("detail", "")
                assert body.get("domain") == domain

            r_b = await _request(app, "GET", path, tenant_id=_TENANT_B)
            assert r_b.status_code == 200, path


@pytest.mark.asyncio
async def test_middleware_cross_tenant_resolves_per_tenant_id() -> None:
    """Tenant A starter denial must not leak allow into Tenant B (or vice versa)."""
    app = _make_entitlement_app()
    seen: list[str] = []

    async def resolve(db: Any, tenant_id: str) -> tuple[Any, dict[str, Any]]:
        seen.append(str(tenant_id))
        tier = "starter" if str(tenant_id) == _TENANT_A else "growth"
        return default_entitlements_for_tier(tier), {"tier": tier, "plan_id": None}

    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(side_effect=resolve),
        ),
        patch("app.modules.admin.entitlement_middleware.UsageMeterService") as meter_cls,
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        meter_cls.return_value.quota_usage_snapshot = AsyncMock(
            return_value={
                "usage": {
                    "seats": 0,
                    "connectors": 0,
                    "ai_tokens": 0,
                    "storage_mb": 0,
                },
                "period": "2026-08",
            }
        )
        denied = await _request(app, "GET", "/api/v1/rag/ask", tenant_id=_TENANT_A)
        allowed = await _request(app, "GET", "/api/v1/rag/ask", tenant_id=_TENANT_B)

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert seen == [_TENANT_A, _TENANT_B]


@pytest.mark.asyncio
async def test_middleware_owner_admin_bypass_even_when_starter() -> None:
    """Owner/admin/auth surfaces must not be plan-gated (CI safety)."""
    app = _make_entitlement_app()

    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(
                return_value=(
                    default_entitlements_for_tier("starter"),
                    {"tier": "starter"},
                )
            ),
        ),
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        cases = (
            ("GET", "/api/v1/admin/tenants"),
            ("POST", "/api/v1/auth/login"),
            ("GET", "/api/v1/owner/me"),
            ("GET", "/health"),
        )
        for method, path in cases:
            r = await _request(app, method, path, tenant_id=_TENANT_A)
            assert r.status_code == 200, path


@pytest.mark.asyncio
async def test_middleware_flags_off_passthrough() -> None:
    app = _make_entitlement_app()
    with (
        patch("app.modules.admin.entitlement_middleware.settings") as mock_settings,
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(side_effect=AssertionError("resolve must not run when flags off")),
        ),
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        mock_settings.entitlement_enforcement_enabled = False
        mock_settings.quota_enforcement_enabled = False
        r = await _request(app, "GET", "/api/v1/rag/ask", tenant_id=_TENANT_A)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_middleware_quota_flag_off_still_domain_denies() -> None:
    """Quota off must not disable domain entitlement denial."""
    app = _make_entitlement_app()
    with (
        patch("app.modules.admin.entitlement_middleware.settings") as mock_settings,
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(
                return_value=(
                    default_entitlements_for_tier("starter"),
                    {"tier": "starter"},
                )
            ),
        ),
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        mock_settings.entitlement_enforcement_enabled = True
        mock_settings.quota_enforcement_enabled = False
        r = await _request(app, "GET", "/api/v1/rag/ask", tenant_id=_TENANT_A)
    assert r.status_code == 403
    assert r.json().get("domain") == "DOM-011"


@pytest.mark.asyncio
async def test_middleware_quota_exceeded_ai_tokens_429() -> None:
    app = _make_entitlement_app()
    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(
                return_value=(
                    default_entitlements_for_tier("growth"),
                    {"tier": "growth", "plan_id": "p-g"},
                )
            ),
        ),
        patch("app.modules.admin.entitlement_middleware.UsageMeterService") as meter_cls,
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        meter_cls.return_value.quota_usage_snapshot = AsyncMock(
            return_value={
                "usage": {
                    "seats": 1,
                    "connectors": 0,
                    "ai_tokens": 500_000,
                    "storage_mb": 1,
                },
                "period": "2026-08",
            }
        )
        r = await _request(app, "POST", "/api/v1/rag/ask", tenant_id=_TENANT_B)
    assert r.status_code == 429
    body = r.json()
    assert body["error"] == "quota_exceeded"
    assert body["metric"] == "ai_tokens"


@pytest.mark.asyncio
async def test_middleware_seat_quota_on_invite_403() -> None:
    app = _make_entitlement_app()
    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(
                return_value=(
                    default_entitlements_for_tier("starter"),
                    {"tier": "starter"},
                )
            ),
        ),
        patch("app.modules.admin.entitlement_middleware.UsageMeterService") as meter_cls,
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        meter_cls.return_value.quota_usage_snapshot = AsyncMock(
            return_value={
                "usage": {
                    "seats": 5,
                    "connectors": 0,
                    "ai_tokens": 0,
                    "storage_mb": 0,
                },
                "period": "2026-08",
            }
        )
        r = await _request(app, "POST", "/api/v1/identity/invite", tenant_id=_TENANT_A)
    assert r.status_code == 403
    assert r.json()["error"] == "quota_exceeded"
    assert r.json()["metric"] == "seats"


@pytest.mark.asyncio
async def test_middleware_connector_quota_blocks_mutate_not_get() -> None:
    app = _make_entitlement_app()
    usage = {
        "usage": {
            "seats": 1,
            "connectors": 1,
            "ai_tokens": 0,
            "storage_mb": 0,
        },
        "period": "2026-08",
    }
    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(
                return_value=(
                    default_entitlements_for_tier("starter"),
                    {"tier": "starter"},
                )
            ),
        ),
        patch("app.modules.admin.entitlement_middleware.UsageMeterService") as meter_cls,
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        meter_cls.return_value.quota_usage_snapshot = AsyncMock(return_value=usage)
        get_r = await _request(app, "GET", "/api/v1/integrations/sync", tenant_id=_TENANT_A)
        post_r = await _request(app, "POST", "/api/v1/integrations/sync", tenant_id=_TENANT_A)
    assert get_r.status_code == 200
    assert post_r.status_code == 403
    assert post_r.json()["error"] == "quota_exceeded"
    assert post_r.json()["metric"] == "connectors"


@pytest.mark.asyncio
async def test_middleware_no_tenant_context_fails_closed_to_auth() -> None:
    """No tenant → do not invent access; leave to auth (pass-through)."""
    app = _make_entitlement_app()
    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(side_effect=AssertionError("must not resolve")),
        ),
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        r = await _request(app, "GET", "/api/v1/rag/ask", tenant_id=None)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_middleware_ungated_contacts_passthrough() -> None:
    app = _make_entitlement_app()
    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(side_effect=AssertionError("ungated must skip resolve")),
        ),
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        r = await _request(app, "GET", "/api/v1/contacts", tenant_id=_TENANT_A)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_middleware_resolve_failure_returns_503_not_open() -> None:
    app = _make_entitlement_app()
    with (
        patch(
            "app.modules.admin.entitlement_middleware.resolve_entitlements_for_tenant",
            new=AsyncMock(side_effect=RuntimeError("db down")),
        ),
        patch(
            "app.modules.admin.entitlement_middleware.get_current_tenant_id_context",
            return_value=None,
        ),
    ):
        r = await _request(app, "GET", "/api/v1/rag/ask", tenant_id=_TENANT_A)
    assert r.status_code == 503
    assert "entitlement" in r.json().get("detail", "").lower()
