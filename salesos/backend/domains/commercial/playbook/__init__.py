"""Playbook domain model — guided selling playbooks for each sales stage."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PlaybookTrigger(str, Enum):
    STAGE_ENTER = "stage_enter"
    SIGNAL_DETECTED = "signal_detected"
    TIME_ELAPSED = "time_elapsed"
    HEALTH_CHANGE = "health_change"
    MANUAL = "manual"


@dataclass
class PlaybookStep:
    """A single step within a playbook."""
    id: str
    action: str  # Maps to NBA action types
    title_ar: str
    title_en: str
    order: int
    stage: str  # Which pipeline stage this step belongs to
    description: str = ""
    estimated_minutes: int = 15
    is_optional: bool = False
    templates: dict[str, str] = field(default_factory=dict)


@dataclass
class Playbook:
    """A playbook — guided set of steps for selling to a specific segment."""
    id: str
    tenant_id: str
    name: str
    description: str
    triggers: list[PlaybookTrigger] = field(default_factory=list)
    steps: list[PlaybookStep] = field(default_factory=list)
    industry: str | None = None  # Industry filter (None = all)
    min_deal_size: float = 0.0
    max_deal_size: float | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def steps_for_stage(self, stage: str) -> list[PlaybookStep]:
        return [s for s in self.steps if s.stage == stage]


# Default playbooks
DEFAULT_PLAYLISTS: list[Playbook] = [
    Playbook(
        id="pb-enterprise-saas",
        tenant_id="default",
        name="Enterprise SaaS",
        description="دليل بيع لحلول SaaS للشركات الكبرى",
        triggers=[PlaybookTrigger.STAGE_ENTER],
        steps=[
            PlaybookStep(id="step-1", action="send_introduction_email", title_ar="أرسل بريد تعريف",
                         title_en="Send Introduction Email", order=1, stage="prospecting",
                         templates={"email": "قالب بريد تعريف للشركات الكبرى"}),
            PlaybookStep(id="step-2", action="schedule_discovery_call", title_ar="جد مكالمة اكتشاف",
                         title_en="Schedule Discovery Call", order=2, stage="qualification",
                         templates={"email": "قالب دعوة اجتماع اكتشاف"}),
            PlaybookStep(id="step-3", action="prepare_demo", title_ar="حضّر عرض توضيحي",
                         title_en="Prepare Demo", order=3, stage="discovery",
                         estimated_minutes=60),
            PlaybookStep(id="step-4", action="send_proposal", title_ar="أرسل عرض السعر",
                         title_en="Send Proposal", order=4, stage="proposal",
                         templates={"proposal": "قالب عرض سعر SaaS"}),
            PlaybookStep(id="step-5", action="review_contract_terms", title_ar="راجع بنود العقد",
                         title_en="Review Contract Terms", order=5, stage="negotiation"),
            PlaybookStep(id="step-6", action="schedule_onboarding", title_ar="جد موعد بدء الخدمة",
                         title_en="Schedule Onboarding", order=6, stage="closed_won"),
        ],
    ),
    Playbook(
        id="pb-smb-quick-close",
        tenant_id="default",
        name="SMB Quick Close",
        description="دورة بيع سريعة للشركات الصغيرة والمتوسطة",
        triggers=[PlaybookTrigger.STAGE_ENTER],
        steps=[
            PlaybookStep(id="sq-1", action="send_introduction_email", title_ar="أرسل بريد تعريف",
                         title_en="Send Intro", order=1, stage="prospecting"),
            PlaybookStep(id="sq-2", action="send_proposal", title_ar="أرسل عرض سعر سريع",
                         title_en="Send Quick Proposal", order=2, stage="qualification",
                         estimated_minutes=30),
            PlaybookStep(id="sq-3", action="schedule_closing_call", title_ar="جد مكالمة إغلاق",
                         title_en="Schedule Closing Call", order=3, stage="proposal"),
        ],
        max_deal_size=100000,
    ),
]


class PlaybookEngine:
    """Matches opportunities to playbooks and provides next steps."""

    def __init__(self, playbooks: list[Playbook] | None = None):
        self._playbooks = playbooks or list(DEFAULT_PLAYLISTS)

    def find_playbook(self, opportunity: Any) -> Playbook | None:
        """Find the best matching playbook for an opportunity."""
        industry = getattr(opportunity, 'industry', None)
        value = getattr(opportunity, 'value', 0)
        for pb in self._playbooks:
            if not pb.is_active:
                continue
            if pb.industry and pb.industry != industry:
                continue
            if value < pb.min_deal_size:
                continue
            if pb.max_deal_size and value > pb.max_deal_size:
                continue
            return pb
        return self._playbooks[0] if self._playbooks else None

    def get_steps(self, playbook_id: str, stage: str) -> list[PlaybookStep]:
        """Get playbook steps for a specific stage."""
        for pb in self._playbooks:
            if pb.id == playbook_id:
                return pb.steps_for_stage(stage)
        return []
