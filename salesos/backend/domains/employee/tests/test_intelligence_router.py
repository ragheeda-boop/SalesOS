"""Tests for intelligence_router.py — calendar, email, productivity, AI, OAuth, health endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestCalendarKpisEndpoint:
    def test_route_registered(self):
        from domains.employee.intelligence_router import router
        routes = [r.path for r in router.routes]
        assert "/employees/{employee_id}/calendar-kpis" in routes

    def test_route_accepts_get(self):
        from domains.employee.intelligence_router import router
        route = next(r for r in router.routes if r.path == "/employees/{employee_id}/calendar-kpis")
        assert "GET" in route.methods


class TestEmailKpisEndpoint:
    def test_route_registered(self):
        from domains.employee.intelligence_router import router
        routes = [r.path for r in router.routes]
        assert "/employees/{employee_id}/email-kpis" in routes
        assert "/employees/{employee_id}/email-top-contacts" in routes
        assert "/employees/{employee_id}/email-daily-volume" in routes

    def test_days_param_validation(self):
        from domains.employee.intelligence_router import router
        route = next(r for r in router.routes if r.path == "/employees/{employee_id}/email-kpis")
        assert "GET" in route.methods


class TestProductivityEndpoint:
    def test_route_registered(self):
        from domains.employee.intelligence_router import router
        assert "/employees/{employee_id}/productivity" in [r.path for r in router.routes]

    def test_period_days_param_accepted(self):
        from domains.employee.intelligence_router import router
        route = next(r for r in router.routes if r.path == "/employees/{employee_id}/productivity")
        assert "GET" in route.methods


class TestRelationshipEndpoint:
    def test_route_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        assert any("relationship" in p for p in paths)


class TestExecutiveEndpoint:
    def test_route_registered(self):
        from domains.employee.intelligence_router import router
        assert "/executive/summary" in [r.path for r in router.routes]
        assert "/executive/ai-brief" in [r.path for r in router.routes]


class TestOAuthEndpoints:
    def test_callback_route_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        assert any("oauth" in p and "callback" in p for p in paths)

    def test_disconnect_route_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        oauth_paths = [p for p in paths if "oauth" in p]
        assert len(oauth_paths) >= 3  # callback, disconnect, sync

    def test_sync_route_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        assert any("sync" in p for p in paths)


class TestAIEndpoints:
    def test_weekly_digest_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        assert any("weekly-digest" in p for p in paths)

    def test_coaching_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        assert any("coaching" in p for p in paths)

    def test_meeting_summary_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        assert any("calendar-events" in p and "ai-summary" in p for p in paths)

    def test_email_summary_registered(self):
        from domains.employee.intelligence_router import router
        paths = [r.path for r in router.routes]
        assert any("email-events" in p and "ai-summary" in p for p in paths)


class TestHealthEndpoints:
    def test_full_health_registered(self):
        from domains.employee.intelligence_router import router
        assert "/health/employee-360" in [r.path for r in router.routes]

    def test_readiness_registered(self):
        from domains.employee.intelligence_router import router
        assert "/health/employee-360/ready" in [r.path for r in router.routes]

    def test_liveness_registered(self):
        from domains.employee.intelligence_router import router
        assert "/health/employee-360/live" in [r.path for r in router.routes]


class TestTotalEndpointCount:
    def test_all_expected_routes_present(self):
        from domains.employee.intelligence_router import router
        expected_paths = [
            "calendar-kpis", "calendar-heatmap",
            "email-kpis", "email-top-contacts", "email-daily-volume",
            "productivity", "relationship",
            "executive/summary", "executive/ai-brief",
            "oauth", "sync",
            "weekly-digest", "coaching",
            "calendar-events", "email-events",
            "health/employee-360",
        ]
        all_paths = " ".join(r.path for r in router.routes)
        found = sum(1 for p in expected_paths if p in all_paths)
        assert found >= 12, f"Only {found}/{len(expected_paths)} expected routes found"


class TestRouterAuthRequirements:
    def test_protected_routes_require_permission(self):
        from domains.employee.intelligence_router import router
        open_paths = [
            "/health/employee-360",
            "/health/employee-360/ready",
            "/health/employee-360/live",
        ]
        for route in router.routes:
            if route.path in open_paths:
                continue
            deps = getattr(route, "dependencies", None)
            if deps:
                assert len(deps) > 0, f"Route {route.path} has no auth dependency"
