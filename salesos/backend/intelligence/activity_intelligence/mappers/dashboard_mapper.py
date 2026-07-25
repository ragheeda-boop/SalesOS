"""Dashboard Mapper — Capability DTO → API response (ADR-012 §3)."""

from __future__ import annotations


class DashboardMapper:
    """Maps Activity Intelligence internal data to Dashboard API response."""

    @staticmethod
    def to_activity_dashboard(data: dict) -> dict:
        """Map raw dashboard data to ActivityDashboardDTO."""
        return {
            "email_count": data.get("email_count", 0),
            "meeting_count": data.get("meeting_count", 0),
            "followup_count": data.get("followup_count", 0),
            "overdue_count": data.get("overdue_count", 0),
            "top_companies": data.get("top_companies", []),
            "engagement_trend": data.get("engagement_trend", []),
        }
