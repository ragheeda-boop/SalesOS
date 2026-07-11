"""DemoModeService — manages demo mode toggle and behavior."""

import os
import json
from pathlib import Path
from typing import Any

DEMO_DATA_PATH = Path(__file__).parent.parent.parent.parent / "demo" / "demo_data.json"


class DemoModeService:
    """Service for managing demo mode state and data."""

    def __init__(self):
        self._enabled: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
        self._demo_data: dict | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value

    def toggle(self) -> bool:
        self._enabled = not self._enabled
        return self._enabled

    def load_demo_data(self) -> dict | None:
        if self._demo_data is not None:
            return self._demo_data
        if not DEMO_DATA_PATH.exists():
            return None
        with open(DEMO_DATA_PATH, "r", encoding="utf-8") as f:
            self._demo_data = json.load(f)
        return self._demo_data

    def reload_demo_data(self) -> dict | None:
        self._demo_data = None
        return self.load_demo_data()

    def get_companies(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("companies", [])

    def get_opportunities(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("opportunities", [])

    def get_meetings(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("meetings", [])

    def get_emails(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("emails", [])

    def get_signals(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("signals", [])

    def get_tasks(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("tasks", [])

    def get_nba_recommendations(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("nba_recommendations", [])

    def get_workflow_templates(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("workflow_templates", [])

    def get_rag_documents(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("rag_documents", [])

    def get_analytics(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("dashboard_analytics", [])

    def get_timeline_events(self) -> list[dict]:
        data = self.load_demo_data()
        if not data:
            return []
        return data.get("timeline_events", [])

    def get_status(self) -> dict:
        data = self.load_demo_data()
        return {
            "demo_mode": self._enabled,
            "demo_data_available": data is not None,
            "companies_count": len(data.get("companies", [])) if data else 0,
            "opportunities_count": len(data.get("opportunities", [])) if data else 0,
            "total_records": sum(data.get("total", {}).values()) if data and "total" in data else 0,
        }

    def get_scenarios(self) -> list[dict]:
        """Return available demo scenarios."""
        return [
            {
                "id": "enterprise_deal",
                "title": "Enterprise Deal Scenario",
                "description": "Show NBA recommendation → Create task → Send email → Close deal",
                "steps": [
                    {"order": 1, "action": "view_nba", "label": "View NBA Recommendation"},
                    {"order": 2, "action": "create_task", "label": "Create Task from Recommendation"},
                    {"order": 3, "action": "send_email", "label": "Send Follow-up Email"},
                    {"order": 4, "action": "close_deal", "label": "Close Won Deal"},
                ],
            },
            {
                "id": "pipeline_review",
                "title": "Pipeline Review Scenario",
                "description": "Show pipeline health → Forecast → Team performance",
                "steps": [
                    {"order": 1, "action": "view_pipeline", "label": "View Pipeline Health"},
                    {"order": 2, "action": "view_forecast", "label": "Review Forecast"},
                    {"order": 3, "action": "team_performance", "label": "Team Performance Analysis"},
                ],
            },
            {
                "id": "company_research",
                "title": "Company Research Scenario",
                "description": "Search company → RAG query → Meeting brief → Email analysis",
                "steps": [
                    {"order": 1, "action": "search_company", "label": "Search Company"},
                    {"order": 2, "action": "rag_query", "label": "RAG Document Query"},
                    {"order": 3, "action": "view_meeting", "label": "View Meeting Brief"},
                    {"order": 4, "action": "email_analysis", "label": "Email Thread Analysis"},
                ],
            },
        ]


_instance: DemoModeService | None = None


def get_demo_mode_service() -> DemoModeService:
    global _instance
    if _instance is None:
        _instance = DemoModeService()
    return _instance
