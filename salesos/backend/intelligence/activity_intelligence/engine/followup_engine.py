"""Follow-up Engine — priority queue and stagnation detection (ADR-012 §3).

Provides:
- Priority queue for companies needing follow-up
- Stagnation detection (no contact for N days)
- Overdue follow-up identification
"""

from __future__ import annotations

from datetime import datetime, timezone

from intelligence.activity_intelligence.contracts.models import FollowUpStatus


class FollowupEngine:
    """Manages follow-up priorities and detects stagnation."""

    def __init__(
        self,
        email_engine=None,
        calendar_engine=None,
        activity_reader=None,
        stagnation_threshold_days: int = 14,
        overdue_threshold_days: int = 7,
    ):
        self._email_engine = email_engine
        self._calendar_engine = calendar_engine
        self._activity_reader = activity_reader
        self.stagnation_threshold_days = stagnation_threshold_days
        self.overdue_threshold_days = overdue_threshold_days

    async def get_status(
        self, company_id: str, tenant_id: str
    ) -> FollowUpStatus:
        """Get follow-up status for a company."""
        status = FollowUpStatus(company_id=company_id)

        now = datetime.now(timezone.utc)

        # Check last outbound email
        if self._email_engine:
            email_metrics = await self._email_engine.get_email_metrics(
                company_id, tenant_id
            )
            last_outbound_days = None
            sent = email_metrics.get("email_count_sent", 0)
            received = email_metrics.get("email_count_received", 0)

            if email_metrics.get("last_email_days") is not None:
                last_outbound_days = email_metrics["last_email_days"]

            if last_outbound_days is not None:
                status.last_outbound_days = last_outbound_days

                if last_outbound_days > self.stagnation_threshold_days:
                    status.need_followup = True
                    status.overdue = last_outbound_days > self.stagnation_threshold_days * 2

            # Determine who is waiting
            if received > sent:
                status.waiting_you = True  # More inbound than outbound = you need to reply
            elif sent > received and last_outbound_days and last_outbound_days > self.overdue_threshold_days:
                status.waiting_customer = True

        # Check last meeting
        if self._calendar_engine:
            meeting_metrics = await self._calendar_engine.get_meeting_metrics(
                company_id, tenant_id
            )
            last_meeting_days = meeting_metrics.get("last_meeting_days")

            if last_meeting_days is not None and last_meeting_days > self.stagnation_threshold_days * 2:
                status.need_followup = True

        # Set priority based on status
        status.priority = self._calculate_priority(status)
        status.assigned = status.need_followup or status.overdue

        return status

    async def get_all_followups(
        self, company_ids: list[str], tenant_id: str
    ) -> list[FollowUpStatus]:
        """Get follow-up status for multiple companies."""
        results = []
        for company_id in company_ids:
            status = await self.get_status(company_id, tenant_id)
            results.append(status)
        return sorted(
            results,
            key=lambda s: (
                0 if s.overdue else 1,
                0 if s.need_followup else 1,
                0 if s.waiting_you else 1,
                s.last_outbound_days or 999,
            ),
        )

    @staticmethod
    def _calculate_priority(status: FollowUpStatus) -> str:
        """Calculate priority level from follow-up status."""
        if status.overdue:
            return "critical"
        if status.waiting_you and (status.last_outbound_days or 0) > 7:
            return "high"
        if status.need_followup:
            return "medium"
        return "low"
