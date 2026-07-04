"""Activity domain models — immutable activities with outcomes, inside sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ActivityType(Enum):
    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    VISIT = "visit"
    PROPOSAL = "proposal"
    DEMO = "demo"
    TASK = "task"
    REMINDER = "reminder"
    NOTE = "note"


class ActivityStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class OutcomeDefinition:
    """Defines a possible outcome for an activity type.

    Each outcome may trigger a business action via the Rule Engine.
    """

    id: str
    label: str
    label_ar: str
    activity_type: ActivityType
    business_action: str = "none"  # "advance_stage" | "update_probability" | "update_value" | "none"
    action_params: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def catalog() -> list[OutcomeDefinition]:
        return OutcomeDefinition._default_catalog()

    @staticmethod
    def _default_catalog() -> list[OutcomeDefinition]:
        return [
            # ── Call outcomes ──
            OutcomeDefinition(id="call_connected", label="Connected", label_ar="تم الاتصال",
                              activity_type=ActivityType.CALL),
            OutcomeDefinition(id="call_no_answer", label="No Answer", label_ar="لا رد",
                              activity_type=ActivityType.CALL),
            OutcomeDefinition(id="call_qualified", label="Qualified", label_ar="مؤهل",
                              activity_type=ActivityType.CALL,
                              business_action="update_probability",
                              action_params={"delta": 0.15}),
            OutcomeDefinition(id="call_rejected", label="Rejected", label_ar="مرفوض",
                              activity_type=ActivityType.CALL),

            # ── Meeting outcomes ──
            OutcomeDefinition(id="meeting_completed", label="Completed", label_ar="تم الاجتماع",
                              activity_type=ActivityType.MEETING),
            OutcomeDefinition(id="meeting_rescheduled", label="Rescheduled", label_ar="أعيد جدولته",
                              activity_type=ActivityType.MEETING),
            OutcomeDefinition(id="meeting_decision_pending", label="Decision Pending", label_ar="بانتظار القرار",
                              activity_type=ActivityType.MEETING),
            OutcomeDefinition(id="meeting_approved", label="Approved", label_ar="تمت الموافقة",
                              activity_type=ActivityType.MEETING,
                              business_action="advance_stage",
                              action_params={"target": "next"}),
            OutcomeDefinition(id="meeting_rejected", label="Rejected", label_ar="مرفوض",
                              activity_type=ActivityType.MEETING),

            # ── Proposal outcomes ──
            OutcomeDefinition(id="proposal_sent", label="Sent", label_ar="أرسل", activity_type=ActivityType.PROPOSAL),
            OutcomeDefinition(id="proposal_opened", label="Opened", label_ar="فتح", activity_type=ActivityType.PROPOSAL),
            OutcomeDefinition(id="proposal_reviewed", label="Reviewed", label_ar="تمت المراجعة",
                              activity_type=ActivityType.PROPOSAL),
            OutcomeDefinition(id="proposal_accepted", label="Accepted", label_ar="مقبول",
                              activity_type=ActivityType.PROPOSAL,
                              business_action="advance_stage",
                              action_params={"target": "next"}),
            OutcomeDefinition(id="proposal_rejected", label="Rejected", label_ar="مرفوض",
                              activity_type=ActivityType.PROPOSAL),

            # ── Demo outcomes ──
            OutcomeDefinition(id="demo_completed", label="Completed", label_ar="تم العرض",
                              activity_type=ActivityType.DEMO),
            OutcomeDefinition(id="demo_interested", label="Interested", label_ar="مهتم",
                              activity_type=ActivityType.DEMO,
                              business_action="update_probability",
                              action_params={"delta": 0.1}),
            OutcomeDefinition(id="demo_not_interested", label="Not Interested", label_ar="غير مهتم",
                              activity_type=ActivityType.DEMO),

            # ── Task outcomes ──
            OutcomeDefinition(id="task_completed", label="Completed", label_ar="تمت",
                              activity_type=ActivityType.TASK),
            OutcomeDefinition(id="task_overdue", label="Overdue", label_ar="متأخرة",
                              activity_type=ActivityType.TASK),

            # ── Email outcomes ──
            OutcomeDefinition(id="email_sent", label="Sent", label_ar="أرسل", activity_type=ActivityType.EMAIL),
            OutcomeDefinition(id="email_replied", label="Replied", label_ar="رد", activity_type=ActivityType.EMAIL),
        ]


@dataclass
class Activity:
    """A single action within a session. Immutable once completed."""

    id: str
    activity_type: ActivityType
    owner_id: str
    owner_name: str = ""
    outcome_id: str = ""
    outcome_label: str = ""
    notes: str = ""
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    status: ActivityStatus = ActivityStatus.SCHEDULED
    external_id: str = ""

    @property
    def is_completed(self) -> bool:
        return self.status == ActivityStatus.COMPLETED


@dataclass
class ActivitySession:
    """A business engagement session — the Aggregate Root.

    Examples:
    - Customer Visit (meeting + demo + notes)
    - Follow-up Call (call + task)
    - Proposal Follow-up (email + call + reminder)
    """

    id: str
    tenant_id: str
    title: str
    target_id: str  # Opportunity, Company, or Contact ID
    target_type: str = "opportunity"  # "opportunity" | "company" | "contact"
    activities: list[Activity] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: ActivityStatus = ActivityStatus.SCHEDULED
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ActivityOutcome:
    """Record of an activity being completed with an outcome.

    This is the event that the Rule Engine consumes.
    """

    activity_id: str
    session_id: str
    activity_type: ActivityType
    outcome_id: str
    outcome_label: str
    business_action: str
    action_params: dict[str, Any]
    target_id: str
    target_type: str
    owner_id: str
    completed_at: datetime
