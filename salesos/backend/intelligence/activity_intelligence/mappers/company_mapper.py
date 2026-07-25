"""Company Mapper — Capability DTO → Company 360 API response (ADR-012 §3)."""

from __future__ import annotations


class CompanyEngagementMapper:
    """Maps Activity Intelligence data to Company 360 API response."""

    @staticmethod
    def to_company_engagement(company_id: str, data: dict) -> dict:
        """Map raw engagement data to CompanyEngagementDTO."""
        score = data.get("score", {}) or {}
        return {
            "company_id": company_id,
            "email_count": score.get("email_count_sent", 0) + score.get("email_count_received", 0),
            "meeting_count": score.get("meeting_count", 0),
            "last_activity": data.get("last_activity"),
            "last_email": data.get("last_email"),
            "last_meeting": data.get("last_meeting"),
            "followup_status": data.get("followup_status", ""),
        }
