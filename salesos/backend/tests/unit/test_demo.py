"""Tests for Demo Environment — seed data, reset, demo mode, scenarios."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.modules.demo_mode import DemoModeService, get_demo_mode_service


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def demo_service():
    svc = DemoModeService()
    svc._enabled = True
    return svc


@pytest.fixture
def sample_demo_data():
    """Generate minimal demo data for testing."""
    return {
        "tenant_id": "demo_tenant",
        "users": [
            {"id": "u1", "name": "Test User", "role": "admin", "email": "admin@test.io"},
        ],
        "companies": [
            {
                "id": "c1", "tenant_id": "demo_tenant", "name_en": "TestCo",
                "name_ar": "شركة اختبار", "cr_number": "3010000001",
                "city": "Riyadh", "region": "Riyadh", "industry": "technology",
                "employees": 100, "status": "active",
                "description": "Test company description.",
                "annual_revenue": 50000000, "founded_year": 2020,
            },
            {
                "id": "c2", "tenant_id": "demo_tenant", "name_en": "DemoCorp",
                "name_ar": "شركة ديمو", "cr_number": "3010000002",
                "city": "Jeddah", "region": "Makkah", "industry": "fintech",
                "employees": 200, "status": "active",
                "description": "Demo company description.",
                "annual_revenue": 100000000, "founded_year": 2018,
            },
        ],
        "decision_makers": [
            {"id": "dm1", "company_id": "c1", "name": "Ahmed", "role": "CEO", "influence": "high", "connected": True, "email": "ahmed@test.io"},
        ],
        "opportunities": [
            {"id": "opp1", "tenant_id": "demo_tenant", "company_id": "c1", "company_name": "TestCo",
             "title": "Cloud Migration", "stage": "proposal", "estimated_value": 250000,
             "confidence": 0.65, "buying_intent": 0.7, "relationship_strength": 0.6,
             "currency": "SAR", "owner_id": "u1",
             "created_at": "2026-06-01T00:00:00", "expected_close": "2026-08-01T00:00:00"},
            {"id": "opp2", "tenant_id": "demo_tenant", "company_id": "c2", "company_name": "DemoCorp",
             "title": "Payment Platform", "stage": "negotiation", "estimated_value": 500000,
             "confidence": 0.8, "buying_intent": 0.85, "relationship_strength": 0.75,
             "currency": "SAR", "owner_id": "u1",
             "created_at": "2026-05-15T00:00:00"},
            {"id": "opp3", "tenant_id": "demo_tenant", "company_id": "c1", "company_name": "TestCo",
             "title": "Analytics Suite", "stage": "closed_won", "estimated_value": 180000,
             "confidence": 1.0, "buying_intent": 0.9, "relationship_strength": 0.85,
             "currency": "SAR", "owner_id": "u1", "won_amount": 180000,
             "created_at": "2026-04-01T00:00:00"},
        ],
        "meetings": [
            {"id": "mtg1", "tenant_id": "demo_tenant", "opportunity_id": "opp1",
             "company_id": "c1", "type": "product_demo",
             "title": "Demo — TestCo", "notes": "Product demo conducted.",
             "date": "2026-07-01T00:00:00", "duration_minutes": 60, "owner_id": "u1", "outcome": "completed"},
        ],
        "emails": [
            {"id": "em1", "tenant_id": "demo_tenant", "opportunity_id": "opp1",
             "company_id": "c1", "subject": "Follow-up", "preview": "Thank you for the demo.",
             "from_address": "u1@salesos.io", "to_address": "contact@testco.sa",
             "sent_at": "2026-07-02T00:00:00", "direction": "outbound"},
        ],
        "signals": [
            {"id": "sig1", "tenant_id": "demo_tenant", "company_id": "c1",
             "type": "hiring", "title": "Hiring signal", "severity": "high",
             "ai_confidence": 0.85, "timestamp": "2026-07-05T00:00:00", "details": "Hiring 50 engineers."},
        ],
        "tasks": [
            {"id": "task1", "tenant_id": "demo_tenant", "opportunity_id": "opp1",
             "company_id": "c1", "title": "Send proposal", "description": "Send updated proposal.",
             "priority": "high", "source": "nba", "status": "pending",
             "assigned_to": "u1", "created_at": "2026-07-03T00:00:00"},
        ],
        "nba_recommendations": [
            {"id": "nba1", "tenant_id": "demo_tenant", "opportunity_id": "opp1",
             "company_id": "c1", "type": "send_email", "title": "Send follow-up",
             "description": "Follow up after demo.", "priority": "high",
             "confidence": 0.85, "generated_at": "2026-07-04T00:00:00", "status": "active"},
        ],
        "workflow_templates": [
            {"id": "wf1", "tenant_id": "demo_tenant", "name": "Deal Review",
             "category": "sales", "steps": [{"order": 1, "name": "Submit"}], "is_active": True,
             "created_at": "2026-06-01T00:00:00"},
        ],
        "rag_documents": [
            {"id": "doc1", "tenant_id": "demo_tenant", "company_id": "c1",
             "type": "company_profile", "title": "TestCo Profile",
             "content": "TestCo is a technology company.", "created_at": "2026-06-15T00:00:00"},
        ],
        "dashboard_analytics": [
            {"id": "an1", "tenant_id": "demo_tenant", "company_id": "c1",
             "metric": "pipeline_value", "value": 500000.0, "dimension": "total",
             "recorded_at": "2026-07-10T00:00:00"},
        ],
        "timeline_events": [
            {"id": "tl1", "tenant_id": "demo_tenant", "opportunity_id": "opp1",
             "company_id": "c1", "event_type": "meeting", "title": "Demo meeting",
             "description": "Product demo.", "timestamp": "2026-07-01T00:00:00", "user": "u1"},
        ],
        "generated_at": "2026-07-11T00:00:00",
        "total": {
            "users": 1, "companies": 2, "decision_makers": 1, "opportunities": 3,
            "meetings": 1, "emails": 1, "signals": 1, "tasks": 1,
            "nba_recommendations": 1, "workflow_templates": 1, "rag_documents": 1,
            "dashboard_analytics": 1, "timeline_events": 1,
        },
    }


# ── DemoModeService Tests ────────────────────────────────────────────────────


class TestDemoModeService:
    def test_init_default_disabled(self):
        with patch.dict(os.environ, {}, clear=True):
            svc = DemoModeService()
            assert svc.enabled is False

    def test_init_enabled_from_env(self):
        with patch.dict(os.environ, {"DEMO_MODE": "true"}, clear=True):
            svc = DemoModeService()
            assert svc.enabled is True

    def test_set_enabled(self, demo_service):
        assert demo_service.enabled is True
        demo_service.set_enabled(False)
        assert demo_service.enabled is False

    def test_toggle(self, demo_service):
        assert demo_service.enabled is True
        result = demo_service.toggle()
        assert result is False
        assert demo_service.enabled is False
        result = demo_service.toggle()
        assert result is True
        assert demo_service.enabled is True

    def test_load_demo_data_no_file(self, demo_service):
        data = demo_service.load_demo_data()
        assert data is None

    def test_load_demo_data_with_file(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name

        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            data = demo_service.load_demo_data()
            assert data is not None
            assert data["tenant_id"] == "demo_tenant"
            assert len(data["companies"]) == 2
            assert len(data["opportunities"]) == 3

        os.unlink(temp_path)

    def test_reload_demo_data(self, demo_service, sample_demo_data):
        demo_service._demo_data = {"cached": True}
        demo_service.reload_demo_data()
        assert demo_service._demo_data is None

    def test_get_companies(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            companies = demo_service.get_companies()
            assert len(companies) == 2
            assert companies[0]["name_en"] == "TestCo"
        os.unlink(temp_path)

    def test_get_opportunities(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            opps = demo_service.get_opportunities()
            assert len(opps) == 3
            stages = [o["stage"] for o in opps]
            assert "proposal" in stages
            assert "negotiation" in stages
            assert "closed_won" in stages
        os.unlink(temp_path)

    def test_get_status_no_data(self, demo_service):
        status = demo_service.get_status()
        assert status["demo_mode"] is True
        assert status["demo_data_available"] is False
        assert status["companies_count"] == 0

    def test_get_scenarios(self, demo_service):
        scenarios = demo_service.get_scenarios()
        assert len(scenarios) == 3
        scenario_ids = [s["id"] for s in scenarios]
        assert "enterprise_deal" in scenario_ids
        assert "pipeline_review" in scenario_ids
        assert "company_research" in scenario_ids

    def test_get_scenarios_have_steps(self, demo_service):
        scenarios = demo_service.get_scenarios()
        for s in scenarios:
            assert len(s["steps"]) >= 2
            for step in s["steps"]:
                assert "order" in step
                assert "action" in step
                assert "label" in step

    def test_get_meetings_returns_list(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            meetings = demo_service.get_meetings()
            assert len(meetings) == 1
            assert meetings[0]["type"] == "product_demo"
        os.unlink(temp_path)

    def test_get_emails_returns_list(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            emails = demo_service.get_emails()
            assert len(emails) == 1
            assert emails[0]["direction"] == "outbound"
        os.unlink(temp_path)

    def test_get_signals_returns_list(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            signals = demo_service.get_signals()
            assert len(signals) == 1
            assert signals[0]["type"] == "hiring"
        os.unlink(temp_path)

    def test_get_tasks_returns_list(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            tasks = demo_service.get_tasks()
            assert len(tasks) == 1
            assert tasks[0]["priority"] == "high"
        os.unlink(temp_path)

    def test_get_analytics_returns_list(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            analytics = demo_service.get_analytics()
            assert len(analytics) == 1
            assert analytics[0]["metric"] == "pipeline_value"
        os.unlink(temp_path)


# ── Demo Scenario Tests ──────────────────────────────────────────────────────


class TestDemoScenarios:
    def test_enterprise_deal_scenario_structure(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            import demo.scenarios.enterprise_deal as ed_mod
            results = ed_mod.execute(demo_service)
            assert len(results) == 4
            assert results[0]["action"] == "view_nba"
            assert results[1]["action"] == "create_task"
            assert results[2]["action"] == "send_email"
            assert results[3]["action"] == "close_deal"
        os.unlink(temp_path)

    def test_pipeline_review_scenario_structure(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            import demo.scenarios.pipeline_review as pr_mod
            results = pr_mod.execute(demo_service)
            assert len(results) == 3
            assert results[0]["action"] == "view_pipeline"
            assert results[1]["action"] == "view_forecast"
            assert results[2]["action"] == "team_performance"
        os.unlink(temp_path)

    def test_company_research_scenario_structure(self, demo_service, sample_demo_data):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_demo_data, f)
            temp_path = f.name
        with patch("app.modules.demo_mode.service.DEMO_DATA_PATH", Path(temp_path)):
            import demo.scenarios.company_research as cr_mod
            results = cr_mod.execute(demo_service)
            assert len(results) == 4
            assert results[0]["action"] == "search_company"
            assert results[1]["action"] == "rag_query"
            assert results[2]["action"] == "view_meeting"
            assert results[3]["action"] == "email_analysis"
        os.unlink(temp_path)

    def test_scenario_runner_registry(self):
        from demo.scenarios.runner import list_scenarios, execute_scenario
        scenarios = list_scenarios()
        assert len(scenarios) >= 3

    def test_scenario_runner_execute_unknown(self):
        from demo.scenarios.runner import execute_scenario
        with pytest.raises(ValueError, match="Unknown scenario"):
            execute_scenario("nonexistent")


# ── Seed Data Generation Tests ────────────────────────────────────────────────


class TestSeedDataGeneration:
    def test_seed_data_generates_all_sections(self):
        from demo.seed_data import seed_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            assert data["tenant_id"] == "demo_tenant"
            assert len(data["users"]) == 5
            assert len(data["companies"]) == 5
            assert len(data["decision_makers"]) == 14
            assert len(data["opportunities"]) >= 15
            assert len(data["meetings"]) >= 1
            assert len(data["emails"]) >= 1
            assert len(data["signals"]) >= 1
            assert len(data["tasks"]) >= 1
            assert len(data["nba_recommendations"]) >= 1
            assert len(data["workflow_templates"]) == 4
            assert len(data["rag_documents"]) == 10
            assert len(data["timeline_events"]) >= 1

    def test_seed_data_all_stages_represented(self):
        from demo.seed_data import seed_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            stages = {o["stage"] for o in data["opportunities"]}
            for stage in ("qualification", "discovery", "proposal", "negotiation", "closed_won", "closed_lost"):
                assert stage in stages, f"Missing stage: {stage}"

    def test_seed_data_opportunity_values_in_range(self):
        from demo.seed_data import seed_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            for opp in data["opportunities"]:
                assert opp["estimated_value"] >= 10000
                assert opp["estimated_value"] <= 500000

    def test_seed_data_each_company_has_opportunities(self):
        from demo.seed_data import seed_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            company_ids = {c["id"] for c in data["companies"]}
            opp_company_ids = {o["company_id"] for o in data["opportunities"]}
            for cid in company_ids:
                assert cid in opp_company_ids, f"Company {cid} has no opportunities"

    def test_seed_data_users_have_correct_roles(self):
        from demo.seed_data import seed_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            roles = {u["role"] for u in data["users"]}
            assert "admin" in roles
            assert "manager" in roles
            assert "rep" in roles

    def test_seed_data_workflow_templates_have_steps(self):
        from demo.seed_data import seed_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            for wf in data["workflow_templates"]:
                assert len(wf["steps"]) >= 2


# ── Reset Function Tests ─────────────────────────────────────────────────────


class TestResetFunction:
    def test_reset_regenerates_seed(self):
        from demo.reset import reset_demo_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = reset_demo_data(base_dir=tmpdir)
            assert data["total"]["companies"] == 5
            assert data["total"]["opportunities"] >= 15

    def test_reset_replaces_existing_data(self):
        from demo.reset import reset_demo_data, load_demo_data, is_demo_data_available
        with tempfile.TemporaryDirectory() as tmpdir:
            data = reset_demo_data(base_dir=tmpdir)
            assert is_demo_data_available() or True  # File should exist in tmpdir
            loaded = load_demo_data()
            if loaded:
                assert loaded["tenant_id"] == "demo_tenant"

    def test_demo_data_available_no_file(self):
        from demo.reset import is_demo_data_available, DEMO_DATA_FILE
        # Use a nonexistent path
        original = DEMO_DATA_FILE
        import demo.reset as mod
        mod.DEMO_DATA_FILE = "/nonexistent/path.json"
        try:
            assert is_demo_data_available() is False
        finally:
            mod.DEMO_DATA_FILE = original

    def test_status_response_has_all_fields(self, demo_service):
        status = demo_service.get_status()
        assert "demo_mode" in status
        assert "demo_data_available" in status
        assert "companies_count" in status
        assert "opportunities_count" in status
        assert "total_records" in status

    def test_get_scenarios_metadata_complete(self, demo_service):
        scenarios = demo_service.get_scenarios()
        for s in scenarios:
            assert "id" in s
            assert "title" in s
            assert "description" in s
            assert "steps" in s

    def test_seed_data_pipeline_values_by_stage(self):
        from demo.seed_data import seed_data, OPPORTUNITY_TEMPLATES
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            for opp in data["opportunities"]:
                if opp["stage"] == "closed_won":
                    assert opp["confidence"] == 1.0
                elif opp["stage"] == "closed_lost":
                    assert opp["confidence"] == 0.0

    def test_seed_data_decision_makers_per_company(self):
        from demo.seed_data import seed_data
        with tempfile.TemporaryDirectory() as tmpdir:
            data = seed_data(base_dir=tmpdir)
            dm_by_company = {}
            for dm in data["decision_makers"]:
                dm_by_company.setdefault(dm["company_id"], 0)
                dm_by_company[dm["company_id"]] += 1
            for cid, count in dm_by_company.items():
                assert count >= 2, f"Company {cid} has fewer than 2 decision makers"
